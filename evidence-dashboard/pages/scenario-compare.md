---
title: Scenario Compare
---

<script>
  if (typeof window !== "undefined") {
    window.localStorage.setItem("showQueries", "false");
  }
</script>


<style>
.compare-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
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
  max-height: 340px;
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

.bubble-bot a {
  color: #2563eb !important;
  text-decoration: underline !important;
}

.bubble-bot a:hover {
  color: #1d4ed8 !important;
}

.empty {
  border: 1px dashed #d1d5db;
  border-radius: 8px;
  padding: 10px;
  color: #6b7280;
  background: #f9fafb;
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

```sql session_options
select
  s.session_id,
  r.run_started_at || ' · ' || s.endpoint || ' · ' || coalesce(s.scenario_label, s.category) as label
from simlab.sessions s
join simlab.runs r on r.run_id = s.run_id
where s.question_key = '${inputs.question_key.value}'
order by r.run_started_at desc
```

```sql default_sessions
select
  session_id,
  row_number() over (order by run_started_at desc) as slot
from (
  select min(s.session_id) as session_id, r.run_started_at
  from simlab.sessions s
  join simlab.runs r on r.run_id = s.run_id
  where s.question_key = '${inputs.question_key.value}'
  group by s.run_id, r.run_started_at
  order by r.run_started_at desc
)
```

```sql meta_a
select r.run_started_at, s.endpoint, s.turns_total, s.handover_flag, s.handover_turn, s.error_count, s.dead_link_count
from simlab.sessions s
join simlab.runs r on r.run_id = s.run_id
where s.session_id = '${inputs.session_a.value}'
```

```sql meta_b
select r.run_started_at, s.endpoint, s.turns_total, s.handover_flag, s.handover_turn, s.error_count, s.dead_link_count
from simlab.sessions s
join simlab.runs r on r.run_id = s.run_id
where s.session_id = '${inputs.session_b.value}'
```

```sql meta_c
select r.run_started_at, s.endpoint, s.turns_total, s.handover_flag, s.handover_turn, s.error_count, s.dead_link_count
from simlab.sessions s
join simlab.runs r on r.run_id = s.run_id
where s.session_id = '${inputs.session_c.value}'
```

```sql chat_a
select turn, role, replace(replace(replace(replace(text, '<p>', ''), '</p>', ''), '<br/>', '<br>'), '<br />', '<br>') as text
from simlab.turns
where session_id = '${inputs.session_a.value}'
order by turn, case when role='user' then 0 else 1 end
```

```sql chat_b
select turn, role, replace(replace(replace(replace(text, '<p>', ''), '</p>', ''), '<br/>', '<br>'), '<br />', '<br>') as text
from simlab.turns
where session_id = '${inputs.session_b.value}'
order by turn, case when role='user' then 0 else 1 end
```

```sql chat_c
select turn, role, replace(replace(replace(replace(text, '<p>', ''), '</p>', ''), '<br/>', '<br>'), '<br />', '<br>') as text
from simlab.turns
where session_id = '${inputs.session_c.value}'
order by turn, case when role='user' then 0 else 1 end
```

```sql judge_a
select judged_at, response_quality, context_coherence, helpfulness,
       handover_assessment, handover_unnecessary, handover_should_have_happened,
       confidence, summary, analysis_notes
from simlab.ai_judgements
where session_id = '${inputs.session_a.value}'
order by judged_at desc
limit 1
```

```sql judge_b
select judged_at, response_quality, context_coherence, helpfulness,
       handover_assessment, handover_unnecessary, handover_should_have_happened,
       confidence, summary, analysis_notes
from simlab.ai_judgements
where session_id = '${inputs.session_b.value}'
order by judged_at desc
limit 1
```

```sql judge_c
select judged_at, response_quality, context_coherence, helpfulness,
       handover_assessment, handover_unnecessary, handover_should_have_happened,
       confidence, summary, analysis_notes
from simlab.ai_judgements
where session_id = '${inputs.session_c.value}'
order by judged_at desc
limit 1
```

<Dropdown data={topic_options} name=question_key value=question_key label=label>
  <DropdownOption value="" valueLabel="Vælg samtaleemne"/>
</Dropdown>


{#if inputs.question_key.value && default_sessions.length > 0}
  {#key default_sessions[0]?.session_id}
  <Grid cols=3>
    <Dropdown data={session_options} name=session_a value=session_id label=label defaultValue={default_sessions[0]?.session_id}>
      <DropdownOption value="" valueLabel="Simulation A"/>
    </Dropdown>
    <Dropdown data={session_options} name=session_b value=session_id label=label defaultValue={default_sessions[1]?.session_id}>
      <DropdownOption value="" valueLabel="Simulation B"/>
    </Dropdown>
    <Dropdown data={session_options} name=session_c value=session_id label=label defaultValue={default_sessions[2]?.session_id}>
      <DropdownOption value="" valueLabel="Simulation C"/>
    </Dropdown>
  </Grid>
  {/key}
{:else if inputs.question_key.value}
  <Grid cols=3>
    <Dropdown data={session_options} name=session_a value=session_id label=label noDefault=true>
      <DropdownOption value="" valueLabel="Simulation A"/>
    </Dropdown>
    <Dropdown data={session_options} name=session_b value=session_id label=label noDefault=true>
      <DropdownOption value="" valueLabel="Simulation B"/>
    </Dropdown>
    <Dropdown data={session_options} name=session_c value=session_id label=label noDefault=true>
      <DropdownOption value="" valueLabel="Simulation C"/>
    </Dropdown>
  </Grid>
{/if}

{#if inputs.question_key.value}
  <div class="compare-grid">
    <div class="compare-card">
      <h4>Simulation A</h4>
      {#if inputs.session_a.value}
        <DataTable data={meta_a} title="Meta" emptyMessage="Ingen metadata for valgt simulation."/>
      {:else}
        <div class="empty">Vælg en samtale i Simulation A.</div>
      {/if}

      {#if inputs.session_a.value && chat_a.length}
        <div class="chat-log">
          {#each chat_a as row}
            {#if row.role === 'user'}
              <div class="bubble-user"><b>Bruger (T{row.turn})</b><br/>{row.text}</div>
            {:else}
              <div class="bubble-bot"><b>Bot (T{row.turn})</b><br/>{@html row.text}</div>
            {/if}
          {/each}
        </div>
      {:else if inputs.session_a.value}
        <div class="empty">Ingen samtale fundet.</div>
      {/if}

      <form method="get" action="/api/judge" target="judge_a_frame" rel="noopener noreferrer" style="margin-top:10px">
        <input type="hidden" name="session_id" value={inputs.session_a.value} />
        <input type="hidden" name="format" value="html" />
        <button type="submit" disabled={!inputs.session_a.value}>Kør AI Judge</button>
      </form>
      <iframe name="judge_a_frame" style="width:100%; min-height:220px; border:1px solid #e5e7eb; border-radius:8px; margin-top:8px"></iframe>

      {#if inputs.session_a.value}
        <DataTable data={judge_a} title="Seneste AI Judge" emptyMessage="AI Judge er ikke kørt endnu."/>
      {/if}
    </div>

    <div class="compare-card">
      <h4>Simulation B</h4>
      {#if inputs.session_b.value}
        <DataTable data={meta_b} title="Meta" emptyMessage="Ingen metadata for valgt simulation."/>
      {:else}
        <div class="empty">Vælg en samtale i Simulation B.</div>
      {/if}

      {#if inputs.session_b.value && chat_b.length}
        <div class="chat-log">
          {#each chat_b as row}
            {#if row.role === 'user'}
              <div class="bubble-user"><b>Bruger (T{row.turn})</b><br/>{row.text}</div>
            {:else}
              <div class="bubble-bot"><b>Bot (T{row.turn})</b><br/>{@html row.text}</div>
            {/if}
          {/each}
        </div>
      {:else if inputs.session_b.value}
        <div class="empty">Ingen samtale fundet.</div>
      {/if}

      <form method="get" action="/api/judge" target="judge_b_frame" rel="noopener noreferrer" style="margin-top:10px">
        <input type="hidden" name="session_id" value={inputs.session_b.value} />
        <input type="hidden" name="format" value="html" />
        <button type="submit" disabled={!inputs.session_b.value}>Kør AI Judge</button>
      </form>
      <iframe name="judge_b_frame" style="width:100%; min-height:220px; border:1px solid #e5e7eb; border-radius:8px; margin-top:8px"></iframe>

      {#if inputs.session_b.value}
        <DataTable data={judge_b} title="Seneste AI Judge" emptyMessage="AI Judge er ikke kørt endnu."/>
      {/if}
    </div>

    <div class="compare-card">
      <h4>Simulation C</h4>
      {#if inputs.session_c.value}
        <DataTable data={meta_c} title="Meta" emptyMessage="Ingen metadata for valgt simulation."/>
      {:else}
        <div class="empty">Vælg en samtale i Simulation C.</div>
      {/if}

      {#if inputs.session_c.value && chat_c.length}
        <div class="chat-log">
          {#each chat_c as row}
            {#if row.role === 'user'}
              <div class="bubble-user"><b>Bruger (T{row.turn})</b><br/>{row.text}</div>
            {:else}
              <div class="bubble-bot"><b>Bot (T{row.turn})</b><br/>{@html row.text}</div>
            {/if}
          {/each}
        </div>
      {:else if inputs.session_c.value}
        <div class="empty">Ingen samtale fundet.</div>
      {/if}

      <form method="get" action="/api/judge" target="judge_c_frame" rel="noopener noreferrer" style="margin-top:10px">
        <input type="hidden" name="session_id" value={inputs.session_c.value} />
        <input type="hidden" name="format" value="html" />
        <button type="submit" disabled={!inputs.session_c.value}>Kør AI Judge</button>
      </form>
      <iframe name="judge_c_frame" style="width:100%; min-height:220px; border:1px solid #e5e7eb; border-radius:8px; margin-top:8px"></iframe>

      {#if inputs.session_c.value}
        <DataTable data={judge_c} title="Seneste AI Judge" emptyMessage="AI Judge er ikke kørt endnu."/>
      {/if}
    </div>
  </div>
{:else}
  <div class="empty" style="margin-top:12px;">Vælg et samtaleemne for at sammenligne simulationer på tværs af kørsler.</div>
{/if}

