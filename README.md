# Hiper Cognigy AI Scraper

Automatisk kvalitetstest af Hipers Cognigy AI-chatbot. Kører 49 kundescenarier mod chatten, genererer opfølgningsspørgsmål via Claude og producerer en kvalitetsrapport.

## Opsætning

```bash
npm install
npx playwright install chromium
```

## Dag 1: Konfiguration

Åbn `config.js` og udfyld koordinater til "Jeg er ikke kunde"-knappen:

```bash
# Tag et screenshot for at finde koordinaterne
node -e "
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ headless: false });
  const p = await b.newPage();
  await p.goto('https://cognigy-assets.hiper.dk/Test-branch-til-soeren/');
  await p.waitForTimeout(3000);
  await p.screenshot({ path: 'screenshot.png' });
  console.log('Screenshot gemt. Åbn screenshot.png og aflæs koordinater.');
})();
"
```

Mål koordinaterne i `screenshot.png` og sæt dem i `config.js`:
```js
IKKE_KUNDE_X: 123,  // pixel fra venstre
IKKE_KUNDE_Y: 456,  // pixel fra top
```

## Workflow

### Phase 1 – Kør alle 49 spørgsmål

```bash
# Test med 3 spørgsmål først
node phase1_scrape.js --limit 3

# Kør alle 49 (natten over på Lenovo)
node phase1_scrape.js
```

Output: `conversations.db` med 49 user + 49 bot rækker.

### Phase 2 – Generer opfølgningsspørgsmål

```bash
python3 phase2_generate.py
```

Copy-paste outputtet ind i Claude Code. Gem svaret som `followups.json`.

### Phase 3 – Kør opfølgninger

```bash
# Test med 1 session
node phase3_followup.js --limit 1

# Kør alle
node phase3_followup.js
```

Output: DB opdateret med turn 2 og 3 for alle sessioner.

### Phase 4 – Kvalitetsanalyse

```bash
python3 phase4_analyze.py
```

Copy-paste outputtet ind i Claude Code. Gem svaret som `rapport.md`.

## Databasestruktur

```sql
conversations (
  id, session_id, category, category_tag,
  turn,      -- 1=første spørgsmål, 2=followup_1, 3=followup_2
  role,      -- 'user' eller 'bot'
  text,
  handover,  -- 1 hvis bot trigget handover
  links,     -- JSON array af URLs i svaret
  timestamp
)
```

## Kategorier

| Kategori | Spørgsmål | Tag |
|----------|-----------|-----|
| SBBU | 4 | SALES_HANDOVER_EXPECTED |
| Øvrige | 4 | - |
| Hastighed | 5 | - |
| Support øvrige | 5 | - |
| Ustabil | 5 | - |
| Offline | 5 | - |
| Regning | 6 | - |
| Flytning/overdragelse | 5 | SALES_HANDOVER_EXPECTED |
| Etablering | 5 | - |
| Udstyr | 5 | - |

`SALES_HANDOVER_EXPECTED` = handover er forventet og tæller ikke negativt i rapporten.

## Session-genoptagelse (Phase 3)

Phase 3 forsøger automatisk `cognigyWebChat.setCognigySessionId()` (Option B).
Hvis Cognigy ikke understøtter dette, falder scriptet tilbage til nyt flow.
Afklar dag 1 om Option B virker – test med `node phase3_followup.js --limit 1`.
