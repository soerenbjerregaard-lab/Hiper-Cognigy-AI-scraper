# Hiper Cognigy AI Scraper

Automatisk test-framework til Hipers Cognigy AI-chatbot. Kører 49 strukturerede kundescenarier mod chatten i parallelle Playwright-sessioner, gemmer samtaler i SQLite og eksporterer til CSV. Formålet er at afdække svaghed i bot-svarene – herunder forkerte handovers, dårlige links og vidensgab.

## Opsætning

```bash
npm install
npx playwright install chromium
```

## Kør en test

```bash
# Kør alle 49 scenarier (default: gpt41 endpoint)
node run.js

# Test med de første 5 scenarier
node run.js --limit 5

# Kør mod et specifikt endpoint
node run.js --endpoint gpt5
node run.js --endpoint gpt41

# Kombiner flag
node run.js --endpoint gpt5 --limit 5 --concurrency 4
```

Output skrives til `exports/conversations-<endpoint>-<HH.MM-DD-MM-YYYY>.csv` og gemmes automatisk i git.
Der skrives også en run-manifest fil: `exports/runmeta-<endpoint>-<HH.MM-DD-MM-YYYY>.json` med endpoint-navn, endpoint-URL og run-konfiguration.

## Kendte endpoints

Defineret i `config.js`:

| Navn | URL |
|---|---|
| `gpt41` | `https://cognigy-assets.hiper.dk/x-scraping-new-prompt-gpt4-1/` |
| `gpt5` | `https://cognigy-assets.hiper.dk/x-scraping-gpt5-endpoint/` |

Nye endpoints tilføjes under `ENDPOINTS` i `config.js`. Skift default med `DEFAULT_ENDPOINT`.

## Workflow

### 1. Kør scenarier
`run.js` åbner parallelle browser-sessioner, sender spørgsmål fra `scenarios.json` (turn 1) og opfølgningsspørgsmål fra `followups.json` (turn 2+), gemmer alt i `conversations.db` og eksporterer til CSV.

### 2. Kvalitetsanalyse (manuelt)
```bash
python3 phase4_analyze.py
```
Printer en struktureret analyseprompt. Copy-paste outputtet ind i Claude Code. Gem resultatet som `rapport.md`.

Claude evaluerer hvert samtaleforløb med scores for:
- `resolution_score` – løste botten problemet? (0-5)
- `context_retention` – husker botten konteksten på tværs af turns? (0-5)
- `handover_triggered` / `handover_justified` – var overdragelsen berettiget?
- `dead_links` – links i bot-svar der ikke virker
- `kb_gap` – hvad manglede botten viden om?
- `hallucination_risk` – opfandt botten faktuelle detaljer?

## Kategorier

| Kategori | Scenarier | Tag |
|---|---|---|
| SBBU | 4 | `SALES_HANDOVER_EXPECTED` |
| Øvrige | 4 | – |
| Hastighed | 5 | – |
| Support øvrige | 5 | – |
| Ustabil | 5 | – |
| Offline | 5 | – |
| Regning | 6 | – |
| Flytning/overdragelse | 5 | `SALES_HANDOVER_EXPECTED` |
| Etablering | 5 | – |
| Udstyr | 5 | – |

`SALES_HANDOVER_EXPECTED` = handover er forventet adfærd og tæller ikke negativt.

## Databasestruktur

```sql
conversations (
  id, session_id, category, category_tag,
  turn,      -- 1=første spørgsmål, 2+=opfølgning
  role,      -- 'user' eller 'bot'
  text,
  handover,  -- 1 hvis bot trigget handover
  links,     -- JSON array af URLs i svaret
  timestamp
)
```

DB nulstilles manuelt før hver ny testkørsel:
```bash
rm conversations.db
```

Alternativt kan du nulstille sim-data sikkert (arkiverer gamle exports først):
```bash
./scripts/reset_sim_data.sh
```

## Deploy

Scriptet køres på Lenovo-serveren (100.124.174.76) via Tailscale.

```bash
# SSH til Lenovo
ssh soeren-bjerregaard@100.124.174.76

# Hent seneste kode
cd ~/Hiper-Cognigy-AI-scraper && git pull

# Kør i baggrunden
nohup node run.js > run.log 2>&1 &

# Følg med i loggen
tail -f run.log
```

Når kørslen er færdig – commit og push CSV fra Lenovo:
```bash
git add exports/ && git commit -m "Add export: ..." && git push
```

## Nøglefiler

| Fil | Rolle |
|---|---|
| `run.js` | Hoved-script – kører alle scenarier parallelt |
| `config.js` | Endpoints, timeouts, handover-markører, DB-sti |
| `scenarios.json` | 49 test-scenarier med kategorier og spørgsmål |
| `followups.json` | Manuelt genererede opfølgningsspørgsmål (turn 2+) |
| `db.js` | SQLite-wrapper |
| `check_links.js` | Automatisk link-validering af bot-svar |
| `dedup.js` | Hjælpeværktøj til at fjerne duplikerede sessioner i DB |
| `phase4_analyze.py` | Prompt-generator til manuel kvalitetsanalyse |
| `exports/` | CSV-eksporter – trackes i git |
