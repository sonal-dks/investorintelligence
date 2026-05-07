from __future__ import annotations

from datetime import UTC, datetime, timedelta


class FundExplorerService:
    def latest_funds(self, rows: list[dict]) -> list[dict]:
        latest: dict[str, dict] = {}
        for row in rows:
            slug = str(row.get("fund_slug") or "")
            if not slug:
                continue
            previous = latest.get(slug)
            if previous is None or self._to_dt(row.get("scraped_at")) > self._to_dt(previous.get("scraped_at")):
                latest[slug] = row
        ordered = sorted(latest.values(), key=lambda x: str(x.get("fund_name") or "").lower())
        return [self._normalize_fund(row) for row in ordered]

    def build_summary(self, funds: list[dict]) -> dict:
        tracked = len(funds)
        ratios = [float(f["expense_ratio"]) for f in funds if f.get("expense_ratio") is not None]
        avg_expense = round(sum(ratios) / len(ratios), 2) if ratios else 0.0
        high_risk = 0
        latest_scraped: datetime | None = None
        for fund in funds:
            risk = str(fund.get("risk_level") or "").lower()
            if risk in {"high", "very high", "moderately high"}:
                high_risk += 1
            dt = self._to_dt(fund.get("scraped_at"))
            if latest_scraped is None or dt > latest_scraped:
                latest_scraped = dt
        return {
            "tracked_funds": tracked,
            "avg_expense_ratio": avg_expense,
            "high_risk_funds": high_risk,
            "last_scraped_at": latest_scraped.isoformat().replace("+00:00", "Z") if latest_scraped else None,
        }

    def _normalize_fund(self, row: dict) -> dict:
        return {
            "fund_slug": str(row.get("fund_slug") or ""),
            "fund_name": str(row.get("fund_name") or ""),
            "category": row.get("category"),
            "nav": self._to_float(row.get("nav")),
            "nav_date": row.get("nav_date"),
            "aum_cr": self._to_float(row.get("aum_cr")),
            "expense_ratio": self._to_float(row.get("expense_ratio")),
            "min_sip": self._to_int(row.get("min_sip")),
            "risk_level": row.get("risk_level"),
            "returns_1y": self._to_float(row.get("returns_1y")),
            "returns_3y": self._to_float(row.get("returns_3y")),
            "returns_5y": self._to_float(row.get("returns_5y")),
            "source_url": row.get("source_url"),
            "scraped_at": row.get("scraped_at"),
        }

    def sample_rows(self) -> list[dict]:
        now = datetime.now(UTC)
        rows: list[dict] = []
        categories = [
            "Large Cap",
            "Mid Cap",
            "Small Cap",
            "Flexi Cap",
            "Debt",
            "Hybrid",
            "ETF/FOF",
            "Sectoral/Thematic",
        ]
        for i in range(30):
            category = categories[i % len(categories)]
            rows.append(
                {
                    "fund_slug": f"fund-{i+1}",
                    "fund_name": f"Sample Fund {i+1}",
                    "category": category,
                    "nav": 100.0 + i,
                    "nav_date": now.date().isoformat(),
                    "aum_cr": 1000.0 + (i * 25),
                    "expense_ratio": 0.45 + ((i % 7) * 0.05),
                    "min_sip": 500 if i % 2 == 0 else 1000,
                    "risk_level": "Moderately High" if i % 6 == 0 else "Moderate",
                    "returns_1y": 8.0 + i * 0.2,
                    "returns_3y": 10.0 + i * 0.15,
                    "returns_5y": None if i == 0 else 12.0 + i * 0.1,
                    "source_url": f"https://groww.in/mutual-funds/sample-fund-{i+1}",
                    "scraped_at": (now - timedelta(hours=i % 3)).isoformat().replace("+00:00", "Z"),
                }
            )
        return rows

    def _to_dt(self, value: object) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        text = str(value or "")
        if not text:
            return datetime.min.replace(tzinfo=UTC)
        return datetime.fromisoformat(text.replace("Z", "+00:00"))

    def _to_float(self, value: object) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _to_int(self, value: object) -> int | None:
        if value is None:
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None
