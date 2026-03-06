---
title: Simulations Overview
---

<script>
  if (typeof window !== "undefined") {
    window.localStorage.setItem("showQueries", "false");
  }
</script>

```sql kpi
select
  count(distinct run_id) as runs,
  count(distinct session_id) as sessions,
  round(avg(handover_flag), 4) as handover_rate_pct,
  round(avg(case when error_count > 0 then 1 else 0 end), 4) as session_error_rate_pct,
  round(avg(case when dead_link_count > 0 then 1 else 0 end), 4) as dead_link_session_rate_pct,
  round(avg(case when turns_total >= 4 then 1 else 0 end), 4) as reach_t4_pct
from simlab.sessions
```

<Grid cols=3>
  <BigValue data={kpi} value=runs title="Total Runs" fmt=num0/>
  <BigValue data={kpi} value=sessions title="Total Sessions" fmt=num0/>
  <BigValue data={kpi} value=handover_rate_pct title="Handover Rate" fmt=pct1/>
  <BigValue data={kpi} value=session_error_rate_pct title="Session Error Rate" fmt=pct1/>
  <BigValue data={kpi} value=dead_link_session_rate_pct title="Sessions with Dead Links" fmt=pct1/>
  <BigValue data={kpi} value=reach_t4_pct title="Reached Turn 4" fmt=pct1/>
</Grid>

```sql runs_over_time
select
  date(run_started_at) as run_date,
  count(*) as runs,
  sum(session_count) as sessions
from simlab.runs
group by 1
order by 1
```

{#if runs_over_time.length > 1}
  <LineChart
    data={runs_over_time}
    x=run_date
    y=sessions
    title="Sessions per Day"
  />
{:else}
  <DataTable data={runs_over_time} title="Sessions per Day (table view)"/>
{/if}

```sql endpoint_summary
select
  endpoint,
  count(*) as sessions,
  round(avg(handover_flag), 4) as handover_rate_pct,
  round(avg(case when error_count > 0 then 1 else 0 end), 4) as error_rate_pct,
  round(avg(case when dead_link_count > 0 then 1 else 0 end), 4) as dead_link_rate_pct,
  round(avg(turns_total), 2) as avg_turns
from simlab.sessions
group by 1
order by sessions desc
```

{#if endpoint_summary.length > 1}
  <BarChart
    data={endpoint_summary}
    x=endpoint
    y=handover_rate_pct
    title="Handover Rate by Endpoint"
  />
{/if}

<DataTable data={endpoint_summary} rows=20 title="Endpoint Summary"/>

```sql run_health
select
  r.run_started_at,
  substr(r.run_id, 1, 8) as run_short,
  r.endpoint,
  r.session_count,
  round(avg(case when s.error_count > 0 then 1 else 0 end), 4) as session_error_rate_pct,
  round(avg(case when s.timeout_count > 0 then 1 else 0 end), 4) as timeout_session_rate_pct,
  round(avg(case when s.dead_link_count > 0 then 1 else 0 end), 4) as dead_link_session_rate_pct,
  round(avg(s.handover_flag), 4) as handover_rate_pct
from simlab.runs r
join simlab.sessions s on s.run_id = r.run_id
group by 1,2,3,4
order by r.run_started_at desc
```

<DataTable data={run_health} rows=50 title="Run Health"/>

