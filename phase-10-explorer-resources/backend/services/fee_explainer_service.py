from __future__ import annotations

from datetime import UTC, datetime


class FeeExplainerService:
    _TITLE_MAP = {
        "exit_load": "Exit Load",
        "expense_ratio": "Expense Ratio",
        "capital_gains": "Capital Gains Tax",
        "stamp_duty": "Stamp Duty",
        "stt": "Securities Transaction Tax (STT)",
    }

    def build_sections(self, rows: list[dict]) -> dict:
        grouped: dict[str, list[dict]] = {}
        latest_updated: datetime | None = None
        source_url: str | None = None
        for row in rows:
            fee_type = str(row.get("fee_type") or "").strip()
            if not fee_type:
                continue
            grouped.setdefault(fee_type, []).append(row)
            dt = self._to_dt(row.get("last_updated"))
            if latest_updated is None or dt > latest_updated:
                latest_updated = dt
            source_url = source_url or row.get("source_url")

        sections = []
        for fee_type in ["exit_load", "expense_ratio", "capital_gains", "stamp_duty", "stt"]:
            items = grouped.get(fee_type, [])
            if not items:
                continue
            sections.append(
                {
                    "fee_type": fee_type,
                    "title": self._TITLE_MAP.get(fee_type, fee_type.replace("_", " ").title()),
                    "items": [
                        {
                            "category": str(item.get("category") or "General"),
                            "description": str(item.get("description") or ""),
                            "typical_range": item.get("typical_range"),
                            "applicable_to": item.get("applicable_to"),
                            "notes": item.get("notes"),
                        }
                        for item in items
                    ],
                }
            )
        return {
            "sections": sections,
            "last_updated": latest_updated.isoformat().replace("+00:00", "Z") if latest_updated else None,
            "source_url": source_url or "https://groww.in",
        }

    def sample_rows(self) -> list[dict]:
        last_updated = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        return [
            {
                "fee_type": "exit_load",
                "category": "Equity Funds",
                "description": "1% if redeemed within 1 year",
                "typical_range": "0-1%",
                "notes": "Varies by scheme",
                "source_url": "https://groww.in",
                "last_updated": last_updated,
            },
            {
                "fee_type": "expense_ratio",
                "category": "Direct Plans",
                "description": "Lower expense as no distributor commission",
                "typical_range": "0.1-0.5%",
                "source_url": "https://groww.in",
                "last_updated": last_updated,
            },
            {
                "fee_type": "expense_ratio",
                "category": "Regular Plans",
                "description": "Higher expense includes distributor trail",
                "typical_range": "1.0-2.5%",
                "source_url": "https://groww.in",
                "last_updated": last_updated,
            },
            {
                "fee_type": "capital_gains",
                "category": "Equity",
                "description": "STCG at 15%, LTCG at 10% above threshold",
                "source_url": "https://groww.in",
                "last_updated": last_updated,
            },
            {
                "fee_type": "stamp_duty",
                "category": "Purchase",
                "description": "0.005% on purchase amount",
                "source_url": "https://groww.in",
                "last_updated": last_updated,
            },
        ]

    def _to_dt(self, value: object) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        text = str(value or "")
        if not text:
            return datetime.min.replace(tzinfo=UTC)
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
