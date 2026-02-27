'use strict';
/**
 * generate-variations.js
 *
 * Læser scenarios.json og genererer en udvidet version (scenarios-extended.json)
 * med persona-baserede Q1-variationer for hvert scenarie.
 *
 * Bruger Node 22's indbyggede fetch – ingen ekstra afhængigheder nødvendigt.
 *
 * Brug:
 *   ANTHROPIC_API_KEY=sk-... node generate-variations.js
 *   ANTHROPIC_API_KEY=sk-... node generate-variations.js --limit 5   # kun første 5
 *   ANTHROPIC_API_KEY=sk-... node generate-variations.js --resume    # fortsæt fra sidst
 *
 * Output: scenarios-extended.json
 * Originale scenarios.json rettes ikke.
 */

const fs   = require('fs');
const path = require('path');

// ─── Konfiguration ────────────────────────────────────────────────────────────

const SCENARIOS_PATH          = path.join(__dirname, 'scenarios.json');
const OUTPUT_PATH             = path.join(__dirname, 'scenarios-extended.json');
const ANTHROPIC_API_URL       = 'https://api.anthropic.com/v1/messages';
const MODEL                   = 'claude-3-5-haiku-20241022'; // Hurtig og billig til generation
const VARIATIONS_PER_SCENARIO = 8;
const DELAY_MS                = 600; // ms mellem API-kald for at undgå rate limiting

// De 8 personas vi vil dække
const PERSONAS = [
  {
    key: 'frustrated',
    label: 'Frustreret kunde',
    urgency: 'high',
    hint: 'skriver med frustration, evt. udråbstegn, korte og kontante sætninger, tydelig utilfredshed',
  },
  {
    key: 'polite_elderly',
    label: 'Høflig ældre',
    urgency: 'low',
    hint: 'formelt og høfligt dansk, usikker på teknologi, skriver i hele og pæne sætninger',
  },
  {
    key: 'tech_savvy',
    label: 'Teknisk kyndig',
    urgency: 'medium',
    hint: 'bruger fagtermer (Mbit, router, gateway, firmware osv.), præcis og konkret i beskrivelsen',
  },
  {
    key: 'vague',
    label: 'Uklar/usikker',
    urgency: 'low',
    hint: 'mangelfuld kontekst, ved ikke hvad problemet præcist er, stiller et halvt spørgsmål',
  },
  {
    key: 'sms_style',
    label: 'Ung, sms-stil',
    urgency: 'medium',
    hint: 'lowercase, ingen tegnsætning, forkortelser, meget kort, evt. emoji, uformelt',
  },
  {
    key: 'work_from_home',
    label: 'Hjemmekontor-ramte',
    urgency: 'high',
    hint: 'nævner at det er kritisk for arbejde, Teams/Zoom møder, at det haster pga. jobbet',
  },
  {
    key: 'new_customer',
    label: 'Ny kunde',
    urgency: 'low',
    hint: 'ved ikke helt hvad Hiper tilbyder, stiller grundlæggende spørgsmål, usikker på processen',
  },
  {
    key: 'impatient',
    label: 'Utålmodig',
    urgency: 'high',
    hint: 'har allerede ventet, prøvet noget selv, eller henvendt sig tidligere – forventer hurtig løsning nu',
  },
];

// ─── CLI args ─────────────────────────────────────────────────────────────────

const args   = process.argv.slice(2);
const limit  = args.includes('--limit') ? parseInt(args[args.indexOf('--limit') + 1], 10) : null;
const resume = args.includes('--resume');

// ─── Helpers ──────────────────────────────────────────────────────────────────

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function callClaude(prompt) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error(
      'ANTHROPIC_API_KEY er ikke sat.\n' +
      'Kør: ANTHROPIC_API_KEY=sk-ant-... node generate-variations.js'
    );
  }

  const res = await fetch(ANTHROPIC_API_URL, {
    method:  'POST',
    headers: {
      'Content-Type':      'application/json',
      'x-api-key':         apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model:      MODEL,
      max_tokens: 1600,
      messages:   [{ role: 'user', content: prompt }],
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Anthropic API ${res.status}: ${body.slice(0, 200)}`);
  }

  const data = await res.json();
  return data.content[0].text;
}

function extractJson(text) {
  // Prøv at udtrække fra ```json ... ``` blok
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fenced) return JSON.parse(fenced[1].trim());
  // Prøv direkte parse af hele svaret
  return JSON.parse(text.trim());
}

// ─── Prompt ───────────────────────────────────────────────────────────────────

function buildPrompt(scenario) {
  const personaLines = PERSONAS
    .map((p, i) => `${i + 1}. "${p.key}" (${p.label}, urgency: ${p.urgency})\n   Stil: ${p.hint}`)
    .join('\n\n');

  return `Du er ekspert i dansk kundeservice og kundedialog for en internetudbyder.

Jeg tester en AI-chatbot for Hiper (dansk ISP). Jeg har dette testscenarie:

Kategori: ${scenario.category}
Originalt åbningsspørgsmål: "${scenario.questions[0]}"
(Resten af samtalen: "${scenario.questions.slice(1).join('" → "')}")

Din opgave: Returner et JSON-objekt med præcis disse tre felter:

1. "topic": Maks 10 ord – hvad handler scenariet om?
2. "intent": Maks 12 ord – hvad forsøger kunden at opnå?
3. "variations": Array med ${PERSONAS.length} objekter, ét per persona nedenfor.

Hvert variations-objekt skal have:
  "persona"  – brug nøglen fra listen
  "urgency"  – "low", "medium" eller "high"
  "q1"       – det alternative åbningsspørgsmål på dansk

Personas:
${personaLines}

Regler for q1:
- Stil PRÆCIS det samme underliggende problem/spørgsmål som originalen
- Skriv naturligt hverdagsdansk – ikke robotagtigt
- Variér længde fra 3 til ca. 30 ord
- Brug ikke specifikke priser eller interne produktnavne
- Variér åbningen – undgå at alle starter med "Hej"
- sms_style: skriv som en ung dansker ville sms'e

Returner KUN råt JSON – ingen markdown, ingen forklaring.`;
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  console.log('📂 Læser scenarios.json...');
  const scenarios = JSON.parse(fs.readFileSync(SCENARIOS_PATH, 'utf8'));

  // Load eksisterende output hvis --resume
  let existingById = {};
  if (resume && fs.existsSync(OUTPUT_PATH)) {
    const existing = JSON.parse(fs.readFileSync(OUTPUT_PATH, 'utf8'));
    existingById   = Object.fromEntries(existing.map(s => [s.id, s]));
    const doneCount = existing.filter(s => s.variations?.length > 0).length;
    console.log(`▶️  Resume: ${doneCount}/${existing.length} scenarier har allerede variationer\n`);
  }

  const toProcess = limit ? scenarios.slice(0, limit) : scenarios;
  console.log(`🚀 Behandler ${toProcess.length} scenarier, ${PERSONAS.length} personas pr. stk.\n`);

  const results     = [];
  let generated     = 0;
  let skipped       = 0;
  let errors        = 0;

  for (const scenario of toProcess) {
    const existing = existingById[scenario.id];

    // Spring over hvis allerede genereret (kun ved --resume)
    if (resume && existing?.variations?.length > 0) {
      results.push(existing);
      skipped++;
      console.log(`  ⏭️  [id ${scenario.id}] ${scenario.category} – allerede genereret`);
      continue;
    }

    const q1Preview = scenario.questions[0].slice(0, 55);
    process.stdout.write(`  ⏳ [id ${String(scenario.id).padStart(2)}] ${scenario.category}: "${q1Preview}"...\n`);

    try {
      const prompt   = buildPrompt(scenario);
      const rawReply = await callClaude(prompt);
      const parsed   = extractJson(rawReply);

      // Validér
      if (!parsed.topic || !parsed.intent || !Array.isArray(parsed.variations)) {
        throw new Error('Mangler topic, intent eller variations i svaret');
      }

      // Tilføj unikke ID'er til variationerne
      parsed.variations = parsed.variations.map((v, i) => ({
        id: `${scenario.id}-v${i + 1}`,
        ...v,
      }));

      results.push({
        ...scenario,
        topic:      parsed.topic,
        intent:     parsed.intent,
        variations: parsed.variations,
      });

      generated++;
      console.log(`  ✅ "${parsed.topic}" (${parsed.variations.length} variationer)`);

    } catch (err) {
      errors++;
      console.error(`  ❌ [id ${scenario.id}] Fejl: ${err.message}`);
      results.push({ ...scenario }); // Gem uændret så vi ikke mister progress
    }

    // Gem løbende efter hvert scenarie (crash-safe)
    fs.writeFileSync(OUTPUT_PATH, JSON.stringify(results, null, 2), 'utf8');

    await sleep(DELAY_MS);
  }

  // Tilføj scenarier der ikke var i toProcess (hvis --limit)
  if (limit) {
    for (const s of scenarios.slice(limit)) {
      results.push(existingById[s.id] || s);
    }
    fs.writeFileSync(OUTPUT_PATH, JSON.stringify(results, null, 2), 'utf8');
  }

  const totalVariations = results.reduce((n, s) => n + (s.variations?.length || 0), 0);

  console.log(`
╔═══════════════════════════════════════╗
║  Færdig!                              ║
╠═══════════════════════════════════════╣
║  Genereret:       ${String(generated).padEnd(18)} ║
║  Sprang over:     ${String(skipped).padEnd(18)} ║
║  Fejl:            ${String(errors).padEnd(18)} ║
║  Total variationer: ${String(totalVariations).padEnd(16)} ║
╠═══════════════════════════════════════╣
║  Output: scenarios-extended.json      ║
╚═══════════════════════════════════════╝

Næste skridt:
  node run.js --scenarios scenarios-extended.json --sample 20
`);
}

main().catch(err => {
  console.error('\nFatal fejl:', err.message);
  process.exit(1);
});
