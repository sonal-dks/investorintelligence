"""ChunkingService — projects structured fund rows into embeddable text chunks.

LLD reference: Phase 02 §Module Breakdown / ChunkingService.
"""

from __future__ import annotations

import logging
import re
from typing import Iterable

from ..models.schemas import Chunk, ChunkMetadata, FEE_EXPLAINER_CORPUS_SLUG

logger = logging.getLogger(__name__)

MIN_CHUNK_LEN = 10
MAX_CHUNK_LEN = 1500
EXIT_LOAD_KEEP = ("exit load",)


def _normalize(text: str | None, max_len: int = MAX_CHUNK_LEN) -> str | None:
    if text is None:
        return None
    t = re.sub(r"\s+", " ", text).strip()
    if not t:
        return None
    if len(t) > max_len:
        t = t[:max_len].rstrip() + "..."
    return t


# Match the canonical Groww rule phrasings (case-insensitive, run-together text safe).
# Examples observed in the live corpus:
#   "Exit load of 1% if redeemed within 1 year"
#   "Exit load of 0.25% if units are redeemed within 30 days"
#   "Exit load of 2.00% shall be applicable if units are redeemed within 6 months"
# Match the canonical "Exit load of N% ... <duration>" rule, accounting for
# Groww's run-together copy where words like "monthsIf" sit without spaces.
# We end the match at year/month/day plurals followed by end-of-segment
# (non-lowercase/non-digit char OR end of string).
_EXIT_LOAD_RULE_RE = re.compile(
    r"exit\s+load\s+of\s+\d+(?:\.\d+)?%[^.]{0,120}?\b(?:year|month|day)s?(?=[^a-z]|$)",
    flags=re.IGNORECASE,
)

# LTCG / STCG / "taxed at N%" patterns.  Matches both the Groww long-form
# "returns are taxed at 20%" and the short-form "LTCG 12.5% above ₹1.25L".
_TAX_KEYWORDS_RE = re.compile(
    r"(LTCG|STCG|long[-\s]term\s+capital\s+gains?|short[-\s]term\s+capital\s+gains?|taxed\s+at\s+\d+(?:\.\d+)?%)",
    flags=re.IGNORECASE,
)


def _extract_tax_rule(tax_text: str | None) -> str | None:
    """Pull tax-rule sentences out of the long Groww copy.

    Splits on punctuation boundaries (``.;``) and keeps any sentence that
    mentions LTCG, STCG, or "taxed at N%".  This catches both:
      "If you redeem within one year, returns are taxed at 20%"
      "LTCG 12.5% above ₹1.25L after 1 year; STCG 20% within 1 year."
    """

    if not tax_text:
        return None
    # Split on sentence terminators followed by whitespace/end so we don't
    # break "12.5%" or "Rs 1.25 lakh" mid-decimal.
    sentences = re.split(r"(?:[.;](?=\s|$))|;", tax_text)
    keep: list[str] = []
    seen: set[str] = set()
    for s in sentences:
        s_stripped = re.sub(r"\s+", " ", s).strip()
        if not s_stripped:
            continue
        if not _TAX_KEYWORDS_RE.search(s_stripped):
            continue
        # Skip glossary-style definitions that explain the term itself
        s_lower = s_stripped.lower()
        if "is categorized" in s_lower or "depending on your holding" in s_lower:
            continue
        if s_lower in seen:
            continue
        seen.add(s_lower)
        keep.append(s_stripped)
    if not keep:
        return None
    return ". ".join(keep) + "."


def _extract_exit_load_rule(exit_load_text: str | None) -> str | None:
    """Pull the active exit-load rule out of Groww's run-together copy.

    Groww embeds glossary text, dated history, and the active rule with no
    consistent punctuation.  We scan the raw text for the canonical
    "Exit load of N% ... <duration>" pattern and dedupe matches.
    """

    if not exit_load_text:
        return None
    matches = _EXIT_LOAD_RULE_RE.findall(exit_load_text)
    if not matches:
        return None
    cleaned: list[str] = []
    seen: set[str] = set()
    for m in matches:
        norm = re.sub(r"\s+", " ", m).strip().rstrip(".")
        if norm and norm.lower() not in seen:
            seen.add(norm.lower())
            cleaned.append(norm)
    if not cleaned:
        return None
    return ". ".join(cleaned) + "."


def _format_returns(fund: dict) -> str | None:
    parts: list[str] = []
    for label, key in (("1Y", "returns_1y"), ("3Y", "returns_3y"), ("5Y", "returns_5y")):
        val = fund.get(key)
        if val is not None:
            parts.append(f"{label}: {val}%")
    if not parts:
        return None
    return f"{fund['fund_name']} returns — {', '.join(parts)}."


def chunk_fund(fund: dict) -> list[Chunk]:
    """Build hybrid (fact + description) chunks for a single fund row."""

    slug = fund.get("fund_slug")
    name = fund.get("fund_name")
    category = fund.get("category")
    scraped_at = str(fund.get("scraped_at") or "")
    source_url = fund.get("source_url")
    if not slug or not name or not category:
        logger.warning(
            "skip_fund_missing_required_fields",
            extra={"fund_slug": slug, "fund_name": name, "category": category},
        )
        return []

    out: list[Chunk] = []

    def add(source_field: str, text: str | None, chunk_type: str = "fact") -> None:
        norm = _normalize(text)
        if norm is None or len(norm) < MIN_CHUNK_LEN:
            return
        out.append(
            Chunk(
                id=f"{slug}::{chunk_type}::{source_field}",
                text=norm,
                metadata=ChunkMetadata(
                    fund_slug=slug,
                    chunk_type=chunk_type,  # type: ignore[arg-type]
                    source_field=source_field,
                    scraped_at=scraped_at,
                    corpus="mutual_fund",
                    fee_type=None,
                    source_url=str(source_url) if source_url else None,
                ),
            )
        )

    add("category", f"{name} is a {category} fund. Category: {category}.", "fact")

    nav = fund.get("nav")
    nav_date = fund.get("nav_date")
    if nav is not None:
        suffix = f" as of {nav_date}" if nav_date else ""
        add("nav", f"NAV of {name}: ₹{nav}{suffix}.")

    aum = fund.get("aum_cr")
    if aum is not None:
        add("aum_cr", f"AUM of {name}: ₹{aum} crores.")

    expense_ratio = fund.get("expense_ratio")
    if expense_ratio is not None:
        add(
            "expense_ratio",
            f"Expense ratio of {name}: {expense_ratio}% (Direct Plan).",
        )

    min_sip = fund.get("min_sip")
    if min_sip is not None:
        add("min_sip", f"Minimum SIP for {name}: ₹{min_sip}.")

    risk = fund.get("risk_level")
    if risk:
        add("risk_level", f"Risk level of {name}: {risk}.")

    returns_text = _format_returns(fund)
    if returns_text:
        add("returns", returns_text)

    exit_rule = _extract_exit_load_rule(fund.get("exit_load_text"))
    if exit_rule:
        add("exit_load", f"Exit load for {name}: {exit_rule}")

    tax_rule = _extract_tax_rule(fund.get("tax_text"))
    if tax_rule:
        add("tax", f"Tax for {name}: {tax_rule}")

    desc_parts: list[str] = [f"{name} ({category})"]
    if nav is not None:
        desc_parts.append(f"NAV ₹{nav}")
    if aum is not None:
        desc_parts.append(f"AUM ₹{aum}Cr")
    if expense_ratio is not None:
        desc_parts.append(f"expense {expense_ratio}%")
    if min_sip is not None:
        desc_parts.append(f"min SIP ₹{min_sip}")
    if risk:
        desc_parts.append(f"risk {risk}")
    if exit_rule:
        desc_parts.append(f"exit load: {exit_rule}")

    description = ". ".join(desc_parts) + "."
    add("combined", description, "description")

    return out


def chunk_funds(funds: Iterable[dict]) -> tuple[list[Chunk], list[str]]:
    """Chunk many funds.  Returns (chunks, skipped_slugs)."""

    chunks: list[Chunk] = []
    skipped: list[str] = []
    for f in funds:
        produced = chunk_fund(f)
        if not produced:
            slug = f.get("fund_slug") or f.get("fund_name") or "<unknown>"
            skipped.append(str(slug))
            continue
        chunks.extend(produced)
    logger.info(
        "chunking_complete",
        extra={"total_chunks": len(chunks), "skipped_funds": len(skipped)},
    )
    return chunks, skipped


_FEE_TYPE_TITLES = {
    "exit_load": "Exit Load",
    "expense_ratio": "Expense Ratio",
    "capital_gains": "Capital Gains Tax",
    "stamp_duty": "Stamp Duty",
    "stt": "Securities Transaction Tax (STT)",
}


def chunk_fee_explainer_rows(rows: Iterable[dict]) -> tuple[list[Chunk], list[str]]:
    """Build one narrative chunk per fee_type from normalized fee_explainer_data rows.

    Returns (chunks, skipped_reasons) — skipped list is diagnostic only.
    """

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        ft = str(row.get("fee_type") or "").strip()
        if not ft:
            continue
        grouped.setdefault(ft, []).append(row)

    chunks: list[Chunk] = []
    skipped: list[str] = []
    for fee_type, items in grouped.items():
        title = _FEE_TYPE_TITLES.get(fee_type, fee_type.replace("_", " ").title())
        lines: list[str] = [
            f"# {title} (mutual fund fees — explainer)",
            "",
            "This passage explains what this fee or tax means in the context of mutual funds. "
            "It is educational, not scheme-specific advice.",
            "",
        ]
        last_updated: str | None = None
        source_url: str | None = None
        for item in sorted(items, key=lambda r: str(r.get("category") or "")):
            cat = str(item.get("category") or "General").strip()
            desc = str(item.get("description") or "").strip()
            if not desc:
                continue
            rng = item.get("typical_range")
            applies = item.get("applicable_to")
            notes = item.get("notes")
            su = item.get("source_url")
            lu = item.get("last_updated")
            if su and not source_url:
                source_url = str(su)
            if lu:
                last_updated = str(lu)
            lines.append(f"## {cat}")
            lines.append(desc)
            if rng:
                lines.append(f"Typical range: {rng}")
            if applies:
                lines.append(f"When it applies: {applies}")
            if notes:
                lines.append(f"Notes: {notes}")
            lines.append("")

        lines.append(f"Source: {source_url or 'https://groww.in'}")
        if last_updated:
            lines.append(f"Last updated: {last_updated}")

        raw_text = "\n".join(lines).strip()
        norm = _normalize(raw_text)
        if norm is None or len(norm) < MIN_CHUNK_LEN:
            skipped.append(f"fee_type_empty:{fee_type}")
            continue

        chunks.append(
            Chunk(
                id=f"fee_explainer::{fee_type}::narrative",
                text=norm,
                metadata=ChunkMetadata(
                    fund_slug=FEE_EXPLAINER_CORPUS_SLUG,
                    chunk_type="description",
                    source_field="narrative",
                    scraped_at=last_updated or "1970-01-01T00:00:00Z",
                    corpus="fee_explainer",
                    fee_type=fee_type,
                    source_url=source_url,
                ),
            )
        )

    logger.info(
        "fee_explainer_chunking_complete",
        extra={"fee_chunks": len(chunks), "skipped": len(skipped)},
    )
    return chunks, skipped
