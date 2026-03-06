---
title: Question Deep Dive
---

<script>
  if (typeof window !== "undefined") {
    window.localStorage.setItem("showQueries", "false");
  }
</script>

<style>
.empty {
  border: 1px dashed #d1d5db;
  border-radius: 8px;
  padding: 12px;
  color: #6b7280;
  background: #f9fafb;
  margin-top: 8px;
}

.chat-log {
  border: 1px solid #e4e4ea;
  border-radius: 10px;
  padding: 10px;
  max-height: 420px;
  overflow-y: auto;
  background: #fafafc;
}

.bubble-user,
.bubble-bot {
  border-radius: 10px;
  padding: 8px 10px;
  margin-bottom: 8px;
  line-height: 1.35;
}

.bubble-user {
  background: #e9f2ff;
  border: 1px solid #c7dcff;
}

.bubble-bot {
  background: #f2f4f7;
  border: 1px solid #dce1e8;
}
</style>

```sql question_options
select
  question_key,
  min(category) || ' · ' || min(first_user_text) as label
from simlab.sessions
group by 1
order by min(category), min(first_user_text)
```

<Dropdown data={question_options} name=question_key value=question_key label=label>
  <DropdownOption value="" valueLabel="Vælg spørgsmål"/>
</Dropdown>

{#if inputs.question_key.value}
```sql question_overview
select
  question_key,
  min(first_user_text) as question_text,
  min(category) as category,
  count(*) as sessions,
  round(avg(handover_flag), 4) as handover_rate_pct,
  round(avg(case when error_count > 0 then 1 else 0 end), 4) as error_rate_pct,
  round(avg(case when dead_link_count > 0 then 1 else 0 end), 4) as dead_link_rate_pct,
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
  round(avg(s.handover_flag), 4) as handover_rate_pct,
  round(avg(case when s.error_count > 0 then 1 else 0 end), 4) as error_rate_pct,
  round(avg(case when s.dead_link_count > 0 then 1 else 0 end), 4) as dead_link_rate_pct,
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
  r.run_started_at || ' · ' || s.endpoint || ' · ' || s.category || ' · ' || s.first_user_text as label
from simlab.sessions s
join simlab.runs r on r.run_id = s.run_id
where s.question_key = '${inputs.question_key.value}'
order by r.run_started_at desc
```

  <Dropdown data={session_options} name=session_id value=session_id label=label>
    <DropdownOption value="" valueLabel="Vælg samtale"/>
  </Dropdown>

  {#if inputs.session_id.value}
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
  replace(replace(replace(replace(text, '<p>', ''), '</p>', ''), '<br>', '\n'), '<br/>', '\n') as text
from simlab.turns
where session_id = '${inputs.session_id.value}'
order by turn, case when role = 'user' then 0 else 1 end
```

    {#if selected_conversation.length}
      <div class="chat-log">
        {#each selected_conversation as row}
          {#if row.role === 'user'}
            <div class="bubble-user"><b>Bruger (T{row.turn})</b><br/>{row.text}</div>
          {:else}
            <div class="bubble-bot"><b>Bot (T{row.turn})</b><br/>{row.text}</div>
          {/if}
        {/each}
      </div>
    {:else}
      <div class="empty">Ingen samtale fundet for den valgte session.</div>
    {/if}
  {:else}
    <div class="empty">Vælg en samtale for at dykke ned i specifik dialog.</div>
  {/if}
{:else}
  <div class="empty">Vælg et spørgsmål for at se performance på tværs af runs.</div>
{/if}
