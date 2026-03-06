import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { DatabaseSync } from 'node:sqlite';
import { json } from '@sveltejs/kit';

const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://100.124.174.76:11434';
const OLLAMA_MODEL = process.env.OLLAMA_MODEL || 'qwen2.5:3b-instruct';
const PROMPT_VERSION = 'v1';

function getDb() {
  const dbPath = path.resolve(process.cwd(), 'sources/simlab/simlab.db');
  return new DatabaseSync(dbPath);
}

function readPromptTemplate() {
  // Resolve relative to this file so it works regardless of cwd
  // Path: src/routes/api/judge/ → up 4 → evidence-dashboard/
  const p = fileURLToPath(new URL('../../../../judge_prompt_v1.txt', import.meta.url));
  return fs.readFileSync(p, 'utf8');
}

function buildTranscript(turns) {
  return turns
    .map((t) => `Turn ${t.turn} [${String(t.role).toUpperCase()}]: ${t.text}`)
    .join('\n\n');
}

function buildPrompt(transcript) {
  const template = readPromptTemplate();
  return template.replace('{{TRANSCRIPT}}', transcript);
}

function normalizeNumber(val, fallback = 0) {
  const n = Number(val);
  return Number.isFinite(n) ? n : fallback;
}

function normalizeJudge(raw) {
  return {
    response_quality: Math.max(1, Math.min(5, normalizeNumber(raw.response_quality, 1))),
    context_coherence: Math.max(1, Math.min(5, normalizeNumber(raw.context_coherence, 1))),
    helpfulness: Math.max(1, Math.min(5, normalizeNumber(raw.helpfulness, 1))),
    handover_assessment: ['correct', 'unnecessary', 'missing', 'n/a'].includes(raw.handover_assessment)
      ? raw.handover_assessment
      : 'n/a',
    handover_should_have_happened: normalizeNumber(raw.handover_should_have_happened, 0) > 0 ? 1 : 0,
    handover_unnecessary: normalizeNumber(raw.handover_unnecessary, 0) > 0 ? 1 : 0,
    dead_links_found: Math.max(0, Math.floor(normalizeNumber(raw.dead_links_found, 0))),
    summary: String(raw.summary || '').slice(0, 500),
    analysis_notes: String(raw.analysis_notes || '').slice(0, 2000),
    confidence: Math.max(0, Math.min(1, normalizeNumber(raw.confidence, 0.5))),
    inconclusive_reason: String(raw.inconclusive_reason || '').slice(0, 300),
  };
}

function escapeHtml(s) {
  return String(s ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function renderJudgeHtml({ sessionId, judgeModel, promptVersion, judge }) {
  const html = `
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif; margin: 0; padding: 12px; background: #fff; color: #111; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px; }
    .card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px; }
    .label { font-size: 12px; color: #666; margin-bottom: 4px; }
    .value { font-size: 16px; font-weight: 600; }
    .block { border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px; margin-top: 8px; white-space: pre-wrap; line-height: 1.35; }
    .meta { font-size: 12px; color: #666; margin-bottom: 8px; }
  </style>
</head>
<body>
  <div class="meta">Session: <b>${escapeHtml(sessionId)}</b> · Model: <b>${escapeHtml(judgeModel)}</b> · Prompt: <b>${escapeHtml(promptVersion)}</b></div>
  <div class="grid">
    <div class="card"><div class="label">Response Quality</div><div class="value">${escapeHtml(judge.response_quality)}</div></div>
    <div class="card"><div class="label">Context Coherence</div><div class="value">${escapeHtml(judge.context_coherence)}</div></div>
    <div class="card"><div class="label">Helpfulness</div><div class="value">${escapeHtml(judge.helpfulness)}</div></div>
    <div class="card"><div class="label">Confidence</div><div class="value">${escapeHtml(judge.confidence)}</div></div>
    <div class="card"><div class="label">Handover Assessment</div><div class="value">${escapeHtml(judge.handover_assessment)}</div></div>
    <div class="card"><div class="label">Dead Links Found</div><div class="value">${escapeHtml(judge.dead_links_found)}</div></div>
  </div>
  <div class="block"><b>Summary</b>\n${escapeHtml(judge.summary)}</div>
  <div class="block"><b>Analysis Notes</b>\n${escapeHtml(judge.analysis_notes)}</div>
  ${judge.inconclusive_reason ? `<div class="block"><b>Inconclusive Reason</b>\n${escapeHtml(judge.inconclusive_reason)}</div>` : ''}
</body>
</html>`;
  return html;
}

async function callJudge(prompt) {
  const res = await fetch(`${OLLAMA_BASE_URL}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: OLLAMA_MODEL,
      prompt,
      stream: false,
      format: 'json',
      options: { temperature: 0 },
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Ollama call failed: ${res.status} ${body.slice(0, 300)}`);
  }

  const body = await res.json();
  const parsed = JSON.parse(body.response);
  return normalizeJudge(parsed);
}

export async function GET({ url }) {
  const sessionId = url.searchParams.get('session_id');
  const responseFormat = url.searchParams.get('format') || 'json';
  if (!sessionId) return json({ error: 'Missing session_id' }, { status: 400 });

  const db = getDb();
  const turns = db
    .prepare(
      `
      SELECT turn, role, text
      FROM turns
      WHERE session_id = ?
      ORDER BY turn, CASE WHEN role = 'user' THEN 0 ELSE 1 END
      `,
    )
    .all(sessionId);

  if (!turns.length) return json({ error: 'Session not found' }, { status: 404 });

  const run = db.prepare('SELECT run_id FROM sessions WHERE session_id = ?').get(sessionId);
  const transcript = buildTranscript(turns);
  const prompt = buildPrompt(transcript);

  let judge;
  try {
    judge = await callJudge(prompt);
  } catch (e) {
    try {
      judge = await callJudge(prompt);
    } catch (retryErr) {
      return json({ error: 'Judge failed after retry', detail: String(retryErr) }, { status: 502 });
    }
  }

  const insert = db.prepare(
    `
    INSERT INTO ai_judgements (
      session_id, run_id, prompt_version, judge_model,
      response_quality, context_coherence, helpfulness,
      handover_assessment, handover_should_have_happened, handover_unnecessary,
      dead_links_found, summary, analysis_notes, confidence, inconclusive_reason, raw_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `,
  );

  insert.run(
    sessionId,
    run?.run_id || null,
    PROMPT_VERSION,
    OLLAMA_MODEL,
    judge.response_quality,
    judge.context_coherence,
    judge.helpfulness,
    judge.handover_assessment,
    judge.handover_should_have_happened,
    judge.handover_unnecessary,
    judge.dead_links_found,
    judge.summary,
    judge.analysis_notes,
    judge.confidence,
    judge.inconclusive_reason,
    JSON.stringify(judge),
  );

  if (responseFormat === 'html') {
    return new Response(
      renderJudgeHtml({
        sessionId,
        judgeModel: OLLAMA_MODEL,
        promptVersion: PROMPT_VERSION,
        judge,
      }),
      { headers: { 'Content-Type': 'text/html; charset=utf-8' } },
    );
  }

  return json({ ok: true, session_id: sessionId, judge_model: OLLAMA_MODEL, prompt_version: PROMPT_VERSION, judge });
}
