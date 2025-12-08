# Architecture

```mermaid
flowchart TD
    U[Frontend\nReact/Vite] -->|Upload CSV| A[/POST /upload_csv/]
    A -->|Parse & insert| DB[(Postgres\ntransactions)]
    A -->|Background thread| C[Classifier\nOllama]
    C -->|Update category| DB
    DB -->|SQL| S[/GET /stats/]
    DB -->|Counts| P[/GET /classification_progress/]
    U -->|Fetch stats & progress| S
    U -->|Reset DB| R[/POST /reset/]
    R --> DB
```

**Notes**
- Classification runs in a background thread; `/classification_progress` reports running state and counts.
- `/stats` aggregates totals, categories, duplicates, 30d activity, monthly trend, and recurring merchants in SQL.
- CSV ingest normalizes dates/amounts before insert, then triggers classification.
