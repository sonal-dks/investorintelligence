# Phase 10 - Mutual Fund Explorer + Resource Hub

Implements:
- `GET /api/funds` and `GET /api/funds/summary`
- `GET /api/resources/fees`
- Frontend Mutual Fund Explorer with search + category filters
- Frontend Resource Hub with Mutual Funds and Fee Explainer tabs
- Source attribution and scrape timestamp visibility
- Edge-case handling for missing returns (`N/A`) and no-results states

## Run backend tests
```bash
cd phase-10-explorer-resources
python -m pytest tests -q
```

## Run frontend
```bash
cd phase-10-explorer-resources/frontend
npm install
npm run dev
```
