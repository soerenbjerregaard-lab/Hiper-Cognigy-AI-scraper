---
title: Question Deep Dive
---

```sql question_options
select
  question_key,
  coalesce(scenario_label || ' · ' || category, category || ' · (unmapped)') as label
from simlab.sessions
group by 1,2
order by label
```

<Dropdown data={question_options} name=question_key value=question_key>
  <DropdownOption value="" valueLabel="Select question"/>
</Dropdown>

```sql question_overview
select
  question_key,
  min(first_user_text) as question_text,
  min(category) as category,
  count(*) as sessions,
  round(avg(handover_flag) * 100, 1) as handover_rate_pct,
  round(avg(case when error_count > 0 then 1 else 0 end) * 100, 1) as error_rate_pct,
  round(avg(case when dead_link_count > 0 then 1 else 0 end) * 100, 1) as dead_link_rate_pct,
  round(avg(turns_total), 2) as avg_turns,
  round(avg(avg_bot_chars), 1) as avg_bot_chars
from simlab.sessions
where question_key = '${inputs.question_key.value}'
group by 1
```

<BigValue data={question_overview} value=sessions title="Sessions for Question" fmt=num0/>

<DataTable data={question_overview} title="Question Performance"/>

```sql by_run
select
  r.run_started_at,
  s.run_id,
  s.endpoint,
  count(*) as sessions,
  round(avg(s.handover_flag) * 100, 1) as handover_rate_pct,
  round(avg(case when s.error_count > 0 then 1 else 0 end) * 100, 1) as error_rate_pct,
  round(avg(case when s.dead_link_count > 0 then 1 else 0 end) * 100, 1) as dead_link_rate_pct,
  round(avg(s.turns_total), 2) as avg_turns
from simlab.sessions s
join simlab.runs r on r.run_id = s.run_id
where s.question_key = '${inputs.question_key.value}'
group by 1,2,3
order by r.run_started_at
```

<LineChart data={by_run} x=run_started_at y=handover_rate_pct series=endpoint title="Handover Rate Trend"/>

<DataTable data={by_run} rows=100 title="Per Run Performance"/>

```sql session_options
select
  s.session_id,
  r.run_started_at || ' · ' || s.endpoint || ' · ' || s.category as label
from simlab.sessions s
join simlab.runs r on r.run_id = s.run_id
where s.question_key = '${inputs.question_key.value}'
order by r.run_started_at desc
```

<Dropdown data={session_options} name=session_id value=session_id>
  <DropdownOption value="" valueLabel="Select conversation"/>
</Dropdown>

```sql selected_session_metrics
select
  s.session_id,
  r.run_started_at,
  s.run_id,
  s.endpoint,
  s.category,
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

<DataTable data={selected_session_metrics} title="Selected Conversation Metrics"/>

```sql selected_conversation
select
  turn,
  role,
  handover,
  case
    when length(text) > 500 then substr(text, 1, 500) || '...'
    else text
  end as text,
  dead_links_json,
  timestamp
from simlab.turns
where session_id = '${inputs.session_id.value}'
order by turn, case when role = 'user' then 0 else 1 end
```

<DataTable data={selected_conversation} rows=200 title="Conversation"/>
