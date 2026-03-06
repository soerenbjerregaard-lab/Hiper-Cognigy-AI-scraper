---
title: AI Judge Config
---

```sql cfg
select config_key, config_value
from simlab.judge_config
order by config_key
```

<DataTable data={cfg} title="Judge Runtime Config"/>

```sql prompt
select config_value as prompt_text
from simlab.judge_config
where config_key = 'judge_prompt'
```

## Prompt Template (v1)

<DataTable data={prompt} title="Prompt Used by /api/judge" rows=1/>

## How scoring is produced

- Local model (default): `qwen2.5:3b-instruct`
- Endpoint: `/api/judge?session_id=<id>`
- Temperature: `0`
- Strict JSON schema enforced server-side
- Retry policy: `1 retry` on invalid/failed judge response
- Stored fields: numeric scores, handover flags, summary, analysis notes, confidence, inconclusive reason
