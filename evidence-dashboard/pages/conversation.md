---
title: Conversation Explorer + AI Judge
---

```sql run_options
select run_id, run_started_at || ' · ' || endpoint as label
from simlab.runs
order by run_started_at desc
```

<Dropdown data={run_options} name=run_id value=run_id>
  <DropdownOption value="" valueLabel="All runs"/>
</Dropdown>

```sql session_options
select
  s.session_id,
  r.run_started_at || ' · ' || s.endpoint || ' · ' || s.category || ' · T' || s.turns_total as label
from simlab.sessions s
join simlab.runs r on r.run_id = s.run_id
where ('${inputs.run_id.value}' = '' or s.run_id = '${inputs.run_id.value}')
order by r.run_started_at desc
```

<Dropdown data={session_options} name=session_id value=session_id>
  <DropdownOption value="" valueLabel="Select conversation"/>
</Dropdown>

```sql session_metrics
select
  s.session_id,
  r.run_started_at,
  s.run_id,
  s.endpoint,
  s.category,
  s.first_user_text,
  s.turns_total,
  s.handover_flag,
  s.handover_turn,
  s.error_count,
  s.timeout_count,
  s.dead_link_turns,
  s.dead_link_count,
  s.avg_bot_chars
from simlab.sessions s
join simlab.runs r on r.run_id = s.run_id
where s.session_id = '${inputs.session_id.value}'
```

<DataTable data={session_metrics} title="Conversation Metrics"/>

```sql full_conversation
select
  turn,
  role,
  handover,
  text,
  dead_links_json,
  timestamp
from simlab.turns
where session_id = '${inputs.session_id.value}'
order by turn, case when role = 'user' then 0 else 1 end
```

<DataTable data={full_conversation} rows=200 title="Full Conversation"/>

## AI Judge

Use this endpoint to score the selected conversation with local Ollama on Lenovo:

`GET /api/judge?session_id=<session_id>`

<form method="get" action="/api/judge" target="_blank" rel="noopener noreferrer">
  <input type="hidden" name="session_id" value={inputs.session_id.value} />
  <button type="submit">Run AI Judge on this conversation</button>
</form>

Selected session endpoint: `/api/judge?session_id={inputs.session_id.value}`

```sql judge_history
select
  judged_at,
  prompt_version,
  judge_model,
  response_quality,
  context_coherence,
  helpfulness,
  handover_assessment,
  handover_should_have_happened,
  handover_unnecessary,
  dead_links_found,
  confidence,
  inconclusive_reason,
  summary
from simlab.ai_judgements
where session_id = '${inputs.session_id.value}'
order by judged_at desc
```

<DataTable data={judge_history} rows=50 title="AI Judge History"/>

```sql latest_judge_notes
select
  judged_at,
  analysis_notes
from simlab.ai_judgements
where session_id = '${inputs.session_id.value}'
order by judged_at desc
limit 1
```

<DataTable data={latest_judge_notes} title="AI Judge Free-text Notes (latest)"/>
