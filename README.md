# Hiper Cognigy AI Scraper

Automatisk test-framework til Hipers Cognigy AI-chatbot. Kører 49 strukturerede kundescenarier mod chatten i parallelle Playwright-sessioner, gemmer samtaler i SQLite og eksporterer til CSV. Formålet er at afdække svaghed i bot-svarene – herunder forkerte handovers, dårlige links og vidensgap.

## Arkitektur

```
run.js  ─────────────────►  exports/*.csv
  │                               │
  │  (Playwright → Cognigy)       │
  ▼                               ▼
conversations.db          scripts/build_simlab_db.py
                                  │
                                  ▼
                             simlab.db  ◄── streamlit_app/
                                              (Streamlit dashboard)
                                              (AI Judge via Ollama)
```

**Server:** Lenovo via Tailscale (`100.124.174.76`)
**Dashboard:** `http://100.124.174.76:8501`
**Repo:** https://github.com/soerenbjerregaard-lab/Hiper-Cognigy-AI-scraper

---

## Opsætning

### Scraper (Node.js)
```bash
npm install
npx playwright install chromium
```

### Dashboard (Python/Streamlit)
```bash
cd streamlit_app
pip install -r requirements.txt
```

### AI Judge (Ollama)
Kræver [Ollama](https://ollama.com) installeret og kørende lokalt på serveren:
```bash
ollama pull llama3.2:1b   # ~1.3 GB – anbefalet på CPU-only server
```

---

## Workflow

### 1. Kør scenarier
```bash
node run.js              # alle 49 scenarier (gpt41 endpoint)
node run.js --limit 5    # test med 5 første
node run.js --endpoint gpt5
node run.js --endpoint gpt41 --limit 10 --concurrency 4
```
Output skrives til `exports/conversations-<endpoint>-<HH.MM-DD-MM-YYYY>.csv`.
En run-manifest gemmes som `exports/runmeta-<endpoint>-<HH.MM-DD-MM-YYYY>.json`.

### 2. Byg analysedatabasen
```bash
python3 scripts/build_simlab_db.py
```
Læser alle CSV'er i `exports/`, matcher mod `scenarios.json` og bygger `simlab.db` med kørsler, sessioner og turns. Kør dette efter hver ny testkørsel for at opdatere dashboardet.

### 3. Åbn Streamlit-dashboard
```bash
cd streamlit_app
streamlit run app.py --server.port 8501
```
Eller i baggrunden på serveren:
```bash
nohup python3 -m streamlit run streamlit_app/app.py --server.port 8501 --server.headless true > /tmp/streamlit.log 2>&1 &
```

Dashboard-sider:
| Side | Funktion |
|---|---|
| 📊 Oversigt | KPI-kort, trend, endpoint-overblik, kørsels-sundhed |
| 🔍 Scenario Compare | Sammenlign op til 3 simulationer side om side |
| 💬 Samtaleudforsker | Browse samtaler, kør AI Judge |
| 📈 Deep Dive | Analysér ét spørgsmål på tværs af alle kørsler |

### 4. AI Judge
I Samtaleudforsker og Scenario Compare kan du klikke **"🤖 Kør AI Judge"** på en samtale.
Modellen (`llama3.2:1b` via Ollama) evaluerer:

| Felt | Beskrivelse |
|---|---|
| `response_quality` | Præcision og korrekthed (1–5) |
| `context_coherence` | Kontekst-hukommelse på tværs af turns (1–5) |
| `helpfulness` | Konkrete næste skridt vs. generiske svar (1–5) |
| `handover_assessment` | `correct` / `unnecessary` / `missing` / `n/a` |
| `summary` | Kort dansk opsummering |
| `analysis_notes` | Konkrete observationer |
| `confidence` | Modellens sikkerhed på vurderingen (0–1) |

> **OBS:** CPU-only inferens tager 2–7 min. Luk tunge applikationer på serveren for bedre hastighed.

---

## Kendte endpoints

Defineret i `config.js`:

| Navn | URL |
|---|---|
| `gpt41` | `https://cognigy-assets.hiper.dk/x-scraping-new-prompt-gpt4-1/` |
| `gpt5` | `https://cognigy-assets.hiper.dk/x-scraping-gpt5-endpoint/` |

Nye endpoints tilføjes under `ENDPOINTS` i `config.js`.

---

## Deploy-flow (OBLIGATORISK)

1. Alle ændringer laves **lokalt** på MacBook
2. `git add`, `commit`, `push` til GitHub
3. SSH til Lenovo → `git pull` → genstart services
4. **Rediger ALDRIG filer direkte på serveren**

```bash
# SSH til Lenovo
ssh soeren-bjerregaard@100.124.174.76

# Hent seneste kode
cd ~/Hiper-Cognigy-AI-scraper && git pull

# Kør scraper i baggrunden
nohup node run.js > /tmp/run.log 2>&1 &
tail -f /tmp/run.log

# Byg analysedatabasen efter kørsel
python3 scripts/build_simlab_db.py

# Genstart dashboard
pkill -f "streamlit run" ; nohup python3 -m streamlit run streamlit_app/app.py \
  --server.port 8501 --server.headless true > /tmp/streamlit.log 2>&1 &
```

## Nulstil sim-data (ny testkørsel)

```bash
./scripts/reset_sim_data.sh   # arkiverer exports/, nulstiller conversations.db og simlab.db
node run.js
python3 scripts/build_simlab_db.py
```

---

## Nøglefiler

| Fil | Rolle |
|---|---|
| `run.js` | Hoved-script – kører alle scenarier parallelt via Playwright |
| `config.js` | Endpoints, timeouts, handover-markører |
| `scenarios.json` | 49 test-scenarier med kategorier og spørgsmål |
| `followups.json` | Opfølgningsspørgsmål per scenarie (turn 2+) |
| `db.js` | SQLite-wrapper til conversations.db |
| `check_links.js` | Automatisk link-validering af bot-svar |
| `dedup.js` | Fjerner duplikerede sessioner fra DB |
| `scripts/build_simlab_db.py` | ETL: CSV-exports → simlab.db |
| `scripts/reset_sim_data.sh` | Nulstil data til ny kørselsrunde |
| `streamlit_app/` | Streamlit-dashboard (4 sider) |
| `streamlit_app/judge.py` | AI Judge – kalder Ollama, gemmer vurderinger |
| `streamlit_app/judge_prompt_v1.txt` | Prompt-skabelon til AI Judge |
| `exports/` | CSV-eksporter – trackes i git |

---

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

---

## Databaseskema (simlab.db)

```sql
runs          – én række per CSV-export (run_id, endpoint, run_started_at, …)
sessions      – én række per chatbot-session (session_id, handover_flag, error_count, …)
turns         – én række per besked-turn (role, text, handover, dead_links_json, …)
scenarios     – spørgsmålsregister med question_key til stabile joins
ai_judgements – AI Judge-vurderinger gemt per session
judge_config  – model og prompt-version der blev brugt
```
