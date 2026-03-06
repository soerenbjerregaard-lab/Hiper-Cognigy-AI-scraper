# Evidence Dashboard for Hiper Cognigy Simulations

This dashboard turns `exports/*.csv` from the scraper into an inspectable simulation lab.

## Views

- `Simulations Overview`: run volume, handover/error/dead-link rates, run health.
- `Question Deep Dive`: lock a specific question and compare outcomes across runs.
- `Conversation Explorer + AI Judge`: inspect full conversation and trigger a local Ollama judge.
- `AI Judge Config`: inspect active judge model and full prompt template.

## Quick start

```bash
cd evidence-dashboard
npm install
npm run data:build
npm run dev
```

Or in one command:

```bash
npm run dev:simlab
```

## Data model

`npm run data:build` creates `sources/simlab/simlab.db` from:

- `../exports/*.csv`
- `../scenarios.json`
- `../scenarios-extended.json`

Tables:

- `runs`
- `sessions`
- `turns`
- `scenarios`
- `ai_judgements`

## AI Judge endpoint

Conversation page exposes:

- `GET /api/judge?session_id=<id>`

Environment variables:

- `OLLAMA_BASE_URL` (default: `http://100.124.174.76:11434`)
- `OLLAMA_MODEL` (default: `qwen2.5:3b-instruct`)

Judge writes to `ai_judgements` and returns JSON.

## Notes

- Judge runs with `temperature: 0` for determinism.
- Rebuild data after new scraper exports.
