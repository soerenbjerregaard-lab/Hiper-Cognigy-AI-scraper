---
title: Conversation Explorer + AI Judge
---

<script>
  if (typeof window !== "undefined") {
    window.localStorage.setItem("showQueries", "false");
  }
</script>

<style>
.chat-log {
  border: 1px solid #e4e4ea;
  border-radius: 10px;
  padding: 12px;
  max-height: 560px;
  overflow-y: auto;
  background: #fafafc;
  margin-top: 8px;
}

.bubble-user,
.bubble-bot {
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 10px;
  line-height: 1.45;
}

.bubble-user {
  background: #e9f2ff;
  border: 1px solid #c7dcff;
}

.bubble-bot {
  background: #f2f4f7;
  border: 1px solid #dce1e8;
}

.bubble-meta {
  font-size: 12px;
  color: #4b5563;
  margin-bottom: 4px;
}

.empty {
  border: 1px dashed #d1d5db;
  border-radius: 8px;
  padding: 12px;
  color: #6b7280;
  background: #f9fafb;
  margin-top: 8px;
}
</style>

```sql run_options
select run_id, run_started_at || ' · ' || endpoint as label
from simlab.runs
order by run_started_at desc
```

```sql session_options
select
  s.session_id,
  r.run_started_at || ' · ' || s.endpoint || ' · ' || s.category || ' · ' || s.first_user_text as label
from simlab.sessions s
join simlab.runs r on r.run_id = s.run_id
where ('${inputs.run_id.value}' = '' or s.run_id = '${inputs.run_id.value}')
order by r.run_started_at desc
```

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

```sql full_conversation
select
  turn,
  role,
  handover,
  replace(replace(replace(replace(text, '<p>', ''), '</p>', ''), '<br>', '\n'), '<br/>', '\n') as text,
  dead_links_json,
  timestamp
from simlab.turns
where session_id = '${inputs.session_id.value}'
order by turn, case when role = 'user' then 0 else 1 end
```

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

```sql latest_judge_notes
select
  judged_at,
  analysis_notes
from simlab.ai_judgements
where session_id = '${inputs.session_id.value}'
order by judged_at desc
limit 1
```

<Dropdown data={run_options} name=run_id value=run_id label=label>
  <DropdownOption value="" valueLabel="Alle kørsler"/>
</Dropdown>

<Dropdown data={session_options} name=session_id value=session_id label=label>
  <DropdownOption value="" valueLabel="Vælg samtale"/>
</Dropdown>

## Conversation Metrics
{#if inputs.session_id.value}
  <DataTable data={session_metrics} emptyMessage="Ingen metrics for valgt samtale."/>
{:else}
  <div class="empty">Vælg en samtale for at se metrics.</div>
{/if}

## Full Conversation
{#if inputs.session_id.value && full_conversation.length}
  <div class="chat-log">
    {#each full_conversation as row}
      {#if row.role === 'user'}
        <div class="bubble-user">
          <div class="bubble-meta"><b>Bruger</b> · T{row.turn}</div>
          <div>{row.text}</div>
        </div>
      {:else}
        <div class="bubble-bot">
          <div class="bubble-meta"><b>Bot</b> · T{row.turn}</div>
          <div>{row.text}</div>
        </div>
      {/if}
    {/each}
  </div>
{:else if inputs.session_id.value}
  <div class="empty">Ingen turns fundet for samtalen.</div>
{:else}
  <div class="empty">Vælg en samtale for at se chatforløbet.</div>
{/if}

## AI Judge
<p>Kør lokal AI Judge på Lenovo via Ollama.</p>

<form method="get" action="/api/judge" target="judge_main" rel="noopener noreferrer">
  <input type="hidden" name="session_id" value={inputs.session_id.value} />
  <input type="hidden" name="format" value="html" />
  <button type="submit" disabled={!inputs.session_id.value}>Kør AI Judge på denne samtale</button>
</form>
<iframe name="judge_main" style="width:100%; min-height:280px; border:1px solid #e5e7eb; border-radius:8px; margin-top:8px"></iframe>

## AI Judge History
{#if inputs.session_id.value}
  <DataTable data={judge_history} rows=50 emptyMessage="Ingen AI Judge-resultater endnu for samtalen."/>
{:else}
  <div class="empty">Vælg en samtale for at se AI Judge-historik.</div>
{/if}

## AI Judge Fritekst (seneste)
{#if inputs.session_id.value}
  <DataTable data={latest_judge_notes} emptyMessage="Ingen fritekst-noter endnu."/>
{:else}
  <div class="empty">Vælg en samtale for at se fritekst-noter.</div>
{/if}
