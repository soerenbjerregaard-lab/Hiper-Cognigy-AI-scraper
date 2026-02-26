# Hiper Cognigy AI Scraper

## Formål
At bygge et automatiseret test-framework til Hipers Cognigy AI-chatbot. Systemet kører strukturerede test-scenarier mod chatten i parallelle sessioner via Playwright, gemmer alle svar i SQLite og eksporterer til CSV. Formålet er at afdække svagshed i bot-svarene – herunder forkerte handovers, dårlige links og vidensgab – med henblik på at løfte svarkvaliteten.

## Arkitektur
- **Udvikling:** MacBook → denne mappe
- **Repo:** https://github.com/soerenbjerregaard-lab/Hiper-Cognigy-AI-scraper
- **Server:** Lenovo via Tailscale (100.124.174.76)
- **Database:** SQLite på serveren (`conversations.db`)

## Workflow

### 1. Kør scenarier
```bash
node run.js              # alle scenarier
node run.js --limit 5   # test med 5 første
```
Åbner parallelle Playwright-sessioner mod Cognigy-chatten. Hvert scenarie sender spørgsmål fra `scenarios.json` (turn 1) og opfølgningsspørgsmål fra `followups.json` (turn 2+). Resultater gemmes i `conversations.db` og eksporteres til CSV.

### 2. Generer opfølgningsspørgsmål (manuelt)
`followups.json` er genereret ved at copy-paste samtaledata ind i Claude Code og gemme outputtet. Filen indeholder to naturlige opfølgningsspørgsmål per scenarie – som en dansk kunde ville stille dem.

### 3. Kvalitetsanalyse (manuelt)
```bash
python3 phase4_analyze.py
```
Printer en struktureret analyseprompt til stdout. Copy-paste outputtet ind i Claude Code. Gem resultatet som `rapport.md`. Claude evaluerer hvert samtaleforløb med scores for løsningskvalitet, kontekst-hukommelse, handover-berettigelse, dead links og hallucinationsrisiko.

## Nøglefiler
| Fil | Rolle |
|---|---|
| `run.js` | Hoved-script – kører alle scenarier parallelt |
| `config.js` | Endpoint, timeouts, handover-markører, DB-sti |
| `scenarios.json` | 49 test-scenarier med kategorier og spørgsmål |
| `followups.json` | Manuelt genererede opfølgningsspørgsmål |
| `db.js` | SQLite-wrapper |
| `check_links.js` | Automatisk link-validering af bot-svar |
| `dedup.js` | Hjælpeværktøj til at fjerne duplikerede sessioner i DB |
| `phase4_analyze.py` | Prompt-generator til manuel kvalitetsanalyse |

## Deploy-flow (OBLIGATORISK)
1. Alle ændringer laves LOKALT i denne mappe
2. `git add`, `commit`, `push` til GitHub
3. SSH til Lenovo → `git pull` → genstart services
4. ALDRIG rediger filer direkte på serveren

## Regler
- Rediger ALDRIG filer direkte på serveren via SSH
- Alle kodeændringer sker lokalt og pushes via git
- SSH til serveren bruges KUN til: `git pull`, genstart services, tjek logs, database queries
- Bekræft git status før og efter arbejde
