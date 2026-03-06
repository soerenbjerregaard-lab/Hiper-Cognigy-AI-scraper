---
title: Scenario Compare
---

<style>
.compare-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 16px;
  margin-top: 12px;
}

.compare-card {
  border: 1px solid #d9d9de;
  border-radius: 12px;
  padding: 12px;
  background: #ffffff;
}

.chat-log {
  border: 1px solid #e4e4ea;
  border-radius: 10px;
  padding: 10px;
  max-height: 380px;
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

.kv {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  margin-top: 10px;
}

.kv > div {
  padding: 8px;
  border-bottom: 1px solid #eceef2;
}

.kv > div:nth-child(odd) {
  border-right: 1px solid #eceef2;
  font-weight: 600;
}
</style>

```sql topic_options
select
  question_key,
  min(category) || ' · ' || min(first_user_text) as label
from simlab.sessions
group by 1
order by min(category), min(first_user_text)
```

<Dropdown data={topic_options} name=question_key value=question_key>
  <DropdownOption value="" valueLabel="Vælg samtaleemne"/>
</Dropdown>

```sql session_options
select
  s.session_id,
  r.run_started_at || ' · ' || s.endpoint || ' · ' || coalesce(s.scenario_label, s.category) as label
from simlab.sessions s
join simlab.runs r on r.run_id = s.run_id
where s.question_key = '${inputs.question_key.value}'
order by r.run_started_at desc
```

<Grid cols=3>
  <Dropdown data={session_options} name=session_a value=session_id>
    <DropdownOption value="" valueLabel="Simulation A"/>
  </Dropdown>
  <Dropdown data={session_options} name=session_b value=session_id>
    <DropdownOption value="" valueLabel="Simulation B"/>
  </Dropdown>
  <Dropdown data={session_options} name=session_c value=session_id>
    <DropdownOption value="" valueLabel="Simulation C"/>
  </Dropdown>
</Grid>

<div class="compare-grid">
  <div class="compare-card">
    <h4>Simulation A</h4>

```sql meta_a
select r.run_started_at, s.run_id, s.endpoint, s.category, s.first_user_text,
       s.turns_total, s.handover_flag, s.handover_turn, s.error_count, s.dead_link_count, s.avg_bot_chars
from simlab.sessions s
join simlab.runs r on r.run_id = s.run_id
where s.session_id = '${inputs.session_a.value}'
```

<DataTable data={meta_a} title="Meta"/>

```sql chat_a
select turn, role, text
from simlab.turns
where session_id = '${inputs.session_a.value}'
order by turn, case when role='user' then 0 else 1 end
```

<div class="chat-log">
{#each chat_a as row}
  {#if row.role === 'user'}
    <div class="bubble-user"><b>User (T{row.turn})</b><br/>{row.text}</div>
  {:else}
    <div class="bubble-bot"><b>Bot (T{row.turn})</b><br/>{row.text}</div>
  {/if}
{/each}
</div>

<form method="get" action="/api/judge" target="judge_a" rel="noopener noreferrer" style="margin-top:10px">
  <input type="hidden" name="session_id" value={inputs.session_a.value} />
  <input type="hidden" name="format" value="html" />
  <button type="submit">Run AI Judge</button>
</form>
<iframe name="judge_a" style="width:100%; min-height:260px; border:1px solid #e5e7eb; border-radius:8px; margin-top:8px"></iframe>

```sql judge_a
select judged_at, response_quality, context_coherence, helpfulness,
       handover_assessment, handover_unnecessary, handover_should_have_happened,
       confidence, summary, analysis_notes
from simlab.ai_judgements
where session_id = '${inputs.session_a.value}'
order by judged_at desc
limit 1
```

<DataTable data={judge_a} title="Latest AI Judge"/>
  </div>

  <div class="compare-card">
    <h4>Simulation B</h4>

```sql meta_b
select r.run_started_at, s.run_id, s.endpoint, s.category, s.first_user_text,
       s.turns_total, s.handover_flag, s.handover_turn, s.error_count, s.dead_link_count, s.avg_bot_chars
from simlab.sessions s
join simlab.runs r on r.run_id = s.run_id
where s.session_id = '${inputs.session_b.value}'
```

<DataTable data={meta_b} title="Meta"/>

```sql chat_b
select turn, role, text
from simlab.turns
where session_id = '${inputs.session_b.value}'
order by turn, case when role='user' then 0 else 1 end
```

<div class="chat-log">
{#each chat_b as row}
  {#if row.role === 'user'}
    <div class="bubble-user"><b>User (T{row.turn})</b><br/>{row.text}</div>
  {:else}
    <div class="bubble-bot"><b>Bot (T{row.turn})</b><br/>{row.text}</div>
  {/if}
{/each}
</div>

<form method="get" action="/api/judge" target="judge_b" rel="noopener noreferrer" style="margin-top:10px">
  <input type="hidden" name="session_id" value={inputs.session_b.value} />
  <input type="hidden" name="format" value="html" />
  <button type="submit">Run AI Judge</button>
</form>
<iframe name="judge_b" style="width:100%; min-height:260px; border:1px solid #e5e7eb; border-radius:8px; margin-top:8px"></iframe>

```sql judge_b
select judged_at, response_quality, context_coherence, helpfulness,
       handover_assessment, handover_unnecessary, handover_should_have_happened,
       confidence, summary, analysis_notes
from simlab.ai_judgements
where session_id = '${inputs.session_b.value}'
order by judged_at desc
limit 1
```

<DataTable data={judge_b} title="Latest AI Judge"/>
  </div>

  <div class="compare-card">
    <h4>Simulation C</h4>

```sql meta_c
select r.run_started_at, s.run_id, s.endpoint, s.category, s.first_user_text,
       s.turns_total, s.handover_flag, s.handover_turn, s.error_count, s.dead_link_count, s.avg_bot_chars
from simlab.sessions s
join simlab.runs r on r.run_id = s.run_id
where s.session_id = '${inputs.session_c.value}'
```

<DataTable data={meta_c} title="Meta"/>

```sql chat_c
select turn, role, text
from simlab.turns
where session_id = '${inputs.session_c.value}'
order by turn, case when role='user' then 0 else 1 end
```

<div class="chat-log">
{#each chat_c as row}
  {#if row.role === 'user'}
    <div class="bubble-user"><b>User (T{row.turn})</b><br/>{row.text}</div>
  {:else}
    <div class="bubble-bot"><b>Bot (T{row.turn})</b><br/>{row.text}</div>
  {/if}
{/each}
</div>

<form method="get" action="/api/judge" target="judge_c" rel="noopener noreferrer" style="margin-top:10px">
  <input type="hidden" name="session_id" value={inputs.session_c.value} />
  <input type="hidden" name="format" value="html" />
  <button type="submit">Run AI Judge</button>
</form>
<iframe name="judge_c" style="width:100%; min-height:260px; border:1px solid #e5e7eb; border-radius:8px; margin-top:8px"></iframe>

```sql judge_c
select judged_at, response_quality, context_coherence, helpfulness,
       handover_assessment, handover_unnecessary, handover_should_have_happened,
       confidence, summary, analysis_notes
from simlab.ai_judgements
where session_id = '${inputs.session_c.value}'
order by judged_at desc
limit 1
```

<DataTable data={judge_c} title="Latest AI Judge"/>
  </div>
</div>
