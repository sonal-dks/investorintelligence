from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import markdown

IST = ZoneInfo("Asia/Kolkata")

_BLOCK_RE = re.compile(
    r"<!--\s*block:([\w_]+)\s*-->(.*?)<!--\s*endblock\s*-->",
    re.DOTALL,
)


@dataclass
class RenderedEmail:
    subject: str
    body_markdown: str
    body_html: str


def _substitute(template: str, ctx: dict[str, str]) -> str:
    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        return ctx.get(key, "")

    return re.sub(r"\{([\w_]+)\}", repl, template)


def parse_blocks(raw: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    for name, body in _BLOCK_RE.findall(raw):
        blocks[name.strip()] = body.strip()
    if not blocks:
        raise ValueError("Email template has no valid <!-- block:NAME --> sections")
    return blocks


class EmailTemplateRenderer:
    def __init__(self, template_path: str) -> None:
        self._path = template_path

    def _load(self) -> dict[str, str]:
        with open(self._path, encoding="utf-8") as f:
            return parse_blocks(f.read())

    def pulse_block_template(self) -> str:
        return self._load()["pulse_block"]

    def render(
        self,
        *,
        role: str,
        ctx: dict[str, str],
        include_pulse: bool,
        pulse_block_raw: str | None,
    ) -> RenderedEmail:
        blocks = self._load()
        subject_key = "subject_user" if role == "user" else "subject_advisor"
        intro_key = "intro_user" if role == "user" else "intro_advisor"
        parts: list[str] = []
        subj = _substitute(blocks[subject_key], ctx)
        parts.append(_substitute(blocks[intro_key], ctx))
        parts.append(_substitute(blocks["booking_details"], ctx))
        if include_pulse and pulse_block_raw:
            parts.append(_substitute(pulse_block_raw, ctx))
        else:
            parts.append(
                "\n\n_Weekly Pulse not available for this period — section omitted._\n"
            )
        parts.append(_substitute(blocks["footer"], ctx))
        body_md = "\n\n---\n\n".join(parts)
        body_html = markdown.markdown(body_md, extensions=["tables", "fenced_code"])
        wrapped = f"<html><body>{body_html}</body></html>"
        return RenderedEmail(subject=subj, body_markdown=body_md, body_html=wrapped)


def format_scheduled_local(iso_utc: str) -> str:
    s = iso_utc.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=IST)
    return dt.astimezone(IST).strftime("%Y-%m-%d %H:%M %Z")


def format_themes(themes: list[dict]) -> str:
    lines: list[str] = []
    for t in themes[:8]:
        name = t.get("theme") or t.get("name") or str(t)
        lines.append(f"- {name}")
    return "\n".join(lines) if lines else "- (none)"
