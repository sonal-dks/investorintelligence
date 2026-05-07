# Phase 09: Weekly Pulse - Edge Cases and Success Criteria

## Detailed Edge Cases
- Data edge: too few reviews for meaningful theme extraction.
- Quality edge: generated summary exceeds 250 words or has not exactly 3 action ideas.
- Theme edge: top theme is generic and not actionable.
- Freshness edge: latest pulse not available when voice greeting needs briefing.
- Bias edge: summary over-amplifies outlier reviews.

## Success Criteria
- Weekly pulse output is under 250 words with exactly 3 action ideas.
- Top themes are persisted with timestamp and retrievable in real time.
- Theme data is consumable by voice greeting and advisor email context.
- Judge validation enforces structure before publication.
- Missing/insufficient review weeks are explicitly marked without fabricated insights.
