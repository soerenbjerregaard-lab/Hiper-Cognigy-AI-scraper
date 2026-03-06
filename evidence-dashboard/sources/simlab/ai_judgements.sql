select *
from ai_judgements

union all

select
  -1 as id,
  null as session_id,
  null as run_id,
  null as prompt_version,
  null as judge_model,
  null as response_quality,
  null as context_coherence,
  null as helpfulness,
  null as handover_assessment,
  null as handover_should_have_happened,
  null as handover_unnecessary,
  null as dead_links_found,
  null as summary,
  null as analysis_notes,
  null as confidence,
  null as inconclusive_reason,
  null as raw_json,
  null as judged_at
where not exists (select 1 from ai_judgements)
