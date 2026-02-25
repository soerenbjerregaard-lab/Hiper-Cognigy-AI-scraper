// Phase 2 – Automatisk opfølgningsgenerering
// Læser alle samtaler fra DB, genererer 2 naturlige follow-up spørgsmål per session
// via Anthropic SDK, og skriver resultatet til followups.json
//
// Kræver: ANTHROPIC_API_KEY miljøvariabel
// Usage:  node phase2_auto.js [--concurrency 3] [--model claude-sonnet-4-6]

const Anthropic = require('@anthropic-ai/sdk');
const fs        = require('fs');
const path      = require('path');
const { openDb } = require('./db');

const arg = (flag, def) => {
  const i = process.argv.indexOf(flag);
  return i !== -1 ? process.argv[i + 1] : def;
};

const CONCURRENCY    = parseInt(arg('--concurrency', '5'), 10);
const MODEL          = arg('--model', 'claude-sonnet-4-6');
const OUTPUT_PATH    = path.join(__dirname, 'followups.json');

const client = new Anthropic();

// ── Systempromt til Claude ────────────────────────────────────────────────────
const SYSTEM_PROMPT = `Du er testdesigner for Hipers kundeservice-chatbot.
Din opgave er at generere realistiske opfølgningsspørgsmål fra en dansk kunde,
baseret på det svar chatbotten allerede har givet.

Regler:
- Skriv som en rigtig kunde ville – naturligt, dansk, hverdagsligt
- Undgå høflige formuleringer som "Mange tak for svaret" – gå direkte til sagen
- Opfølgning 1: Kunden forstod ikke svaret / vil have uddybning / er lidt frustreret
- Opfølgning 2: Et logisk relateret problem der naturligt følger af situationen

Returner KUN et JSON-objekt – ingen tekst udenfor JSON:
{
  "followup_1": "...",
  "followup_2": "..."
}`;

function buildUserPrompt(session) {
  // Strip HTML tags fra bot-svaret
  const cleanAnswer = session.bot_answer
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&#x[0-9A-Fa-f]+;/g, match => String.fromCodePoint(parseInt(match.slice(3, -1), 16)))
    .trim();

  return `KATEGORI: ${session.category}
KUNDENS SPØRGSMÅL: ${session.question}
BOTENS SVAR: ${cleanAnswer.slice(0, 600)}${cleanAnswer.length > 600 ? '...' : ''}

Generer 2 opfølgningsspørgsmål. Returner kun JSON.`;
}

async function generateFollowups(session) {
  const response = await client.messages.create({
    model:      MODEL,
    max_tokens: 300,
    system:     SYSTEM_PROMPT,
    messages: [{ role: 'user', content: buildUserPrompt(session) }],
  });

  const raw = response.content[0].text.trim();
  // Udtræk JSON selv hvis der er wrapper-tekst
  const jsonMatch = raw.match(/\{[\s\S]*\}/);
  if (!jsonMatch) throw new Error(`Ingen JSON i svar: ${raw.slice(0, 100)}`);
  return JSON.parse(jsonMatch[0]);
}

async function main() {
  if (!process.env.ANTHROPIC_API_KEY) {
    console.error('FEJL: Sæt ANTHROPIC_API_KEY miljøvariabel');
    process.exit(1);
  }

  const db = openDb();

  // Hent alle 49 sessioner med spørgsmål + bot-svar
  const sessions = db.prepare(`
    SELECT
      session_id,
      category,
      category_tag,
      MAX(CASE WHEN role='user' THEN text END) AS question,
      MAX(CASE WHEN role='bot'  THEN text END) AS bot_answer
    FROM conversations
    WHERE turn = 1
    GROUP BY session_id
    ORDER BY category, session_id
  `).all();

  if (sessions.length === 0) {
    console.error('FEJL: Ingen sessioner i DB. Kør phase1_scrape.js først.');
    process.exit(1);
  }

  console.log(`\n=== Phase 2 – Automatisk followup-generering ===`);
  console.log(`Model: ${MODEL} | Sessioner: ${sessions.length} | Parallelitet: ${CONCURRENCY}\n`);

  const results   = new Array(sessions.length);
  const queue     = sessions.map((s, i) => ({ session: s, index: i }));
  const counter   = { done: 0 };
  let   errorCount = 0;

  async function worker() {
    while (queue.length > 0) {
      const item = queue.shift();
      if (!item) break;
      const { session, index } = item;

      try {
        const followups = await generateFollowups(session);

        results[index] = {
          session_id:        session.session_id,
          category:          session.category,
          category_tag:      session.category_tag || null,
          original_question: session.question,
          bot_answer_preview: session.bot_answer
            .replace(/<[^>]+>/g, ' ')
            .replace(/\s+/g, ' ')
            .trim()
            .slice(0, 200),
          followup_1: followups.followup_1,
          followup_2: followups.followup_2,
        };

        counter.done++;
        console.log(`[${String(counter.done).padStart(2)}/${sessions.length}] ✓ ${session.category.padEnd(22)} "${followups.followup_1.slice(0, 50)}..."`);
      } catch (err) {
        errorCount++;
        counter.done++;
        console.log(`[${String(counter.done).padStart(2)}/${sessions.length}] ✗ ${session.category} – ${err.message.slice(0, 60)}`);

        // Fallback: generiske opfølgninger
        results[index] = {
          session_id:        session.session_id,
          category:          session.category,
          category_tag:      session.category_tag || null,
          original_question: session.question,
          bot_answer_preview: '',
          followup_1: 'Kan du forklare det på en anden måde? Jeg forstår det ikke helt.',
          followup_2: 'Hvad gør jeg hvis det ikke virker?',
        };
      }
    }
  }

  await Promise.all(Array.from({ length: CONCURRENCY }, () => worker()));

  // Filtrer null-entries (skulle ikke ske) og gem
  const output = results.filter(Boolean);
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(output, null, 2), 'utf8');

  console.log(`\n=== Færdig ===`);
  console.log(`Succes: ${sessions.length - errorCount} | Fejl: ${errorCount}`);
  console.log(`Gemt: ${OUTPUT_PATH} (${output.length} entries)\n`);
}

main().catch(err => { console.error('Fatal:', err); process.exit(1); });
