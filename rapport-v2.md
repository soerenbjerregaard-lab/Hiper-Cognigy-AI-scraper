# Cognigy Quality Loop – Analyserapport v2

**Dato:** 26. februar 2026
**Analyseret af:** Claude Opus 4.6
**Datakilde:** 103 sessions (402 beskeder) fra `conversations-09.24-26-02-2026.csv`
**Endpoint:** `https://cognigy-assets.hiper.dk/Test-branch-til-soeren/`
**Ændringer vs. v1:** Op til 4 turns per session (var 3), dead link-verifikation, 49 ekstra single-turn sessions

---

## Executive Summary

Hipers Cognigy-chatbot scorer **3.23 / 5** på resolution (samlet) og **3.19 / 5** på kontekstforståelse (multi-turn). Botten performer stærkest på Etablering (4.0) og Flytning (4.1) og svagest på Ustabil (2.1) og Øvrige (2.0). 23% af samtalerne (24/103) er GPT5-kandidater.

**Fem kritiske fund:**

1. **Systematisk tomt Turn 2-svar** – Alle 54 multi-turn sessions har tomme bot-svar i turn 2. Det er en scraper/session-resumption-fejl der bør fikses inden næste kørsel.
2. **5 døde links verificeret** – Botten serverer dead links til kunder i 6 sessions. Heraf er 2 links kritiske (offline-hjælp og opsigelsesside).
3. **Handover-fejlkalibrering** – 22 sessions mangler handover (primært Flytning: 9/10 og SBBU: 7/12). 58 sessions har unødvendig handover-markering.
4. **Multi-turn degradering** – Resolution falder fra 3.39 (single-turn) til 3.09 (multi-turn). Botten klarer simple spørgsmål bedre end samtaler.
5. **Ustabil og Øvrige er kritisk svage** – Gennemsnit på 2.1 og 2.0. Botten mangler viden om produktskifte, streaming-fejlsøgning og eskalering.

---

## 1. Resolution Score

### Samlet per kategori

| Kategori | Single-turn | Multi-turn | Samlet | n |
|---|---|---|---|---|
| **Flytning/overdragelse** | 3.80 | **4.40** | **4.10** | 10 |
| **Etablering** | 3.60 | **4.40** | **4.00** | 10 |
| Hastighed | 3.20 | 4.00 | 3.60 | 10 |
| Regning | 3.67 | 3.50 | 3.58 | 12 |
| Support øvrige | 3.40 | 2.60 | 3.00 | 10 |
| SBBU | **4.00** | 3.00 | 3.33 | 12 |
| Offline | 2.80 | 3.80 | 3.30 | 10 |
| Udstyr | **4.20** | 2.00 | 3.10 | 10 |
| Ustabil | 2.00 | 2.20 | **2.10** | 10 |
| Øvrige | 3.25 | 1.00 | **2.00** | 9 |
| **SAMLET** | **3.39** | **3.09** | **3.23** | 103 |

**Observation:** SBBU og Udstyr scorer højt single-turn (4.0, 4.2) men falder kraftigt multi-turn (3.0, 2.0). Botten giver et godt førstesvar men fejler ved opfølgning. Øvrige falder helt til 1.0 multi-turn – her har botten nærmest ingen brugbar viden.

### Scorefordeling (alle 103 sessions)

| Score | Antal | Andel |
|---|---|---|
| 5 – Fuldt løst | 16 | 16% |
| 4 – Løst med omveje | 34 | 33% |
| 3 – Delvist svar | 23 | 22% |
| 2 – Relateret men uhjælpsomt | 20 | 19% |
| 1 – Off-topic/forvirrende | 8 | 8% |
| 0 – Ingen hjælp | 2 | 2% |

---

## 2. Kontekstforståelse (multi-turn, 54 sessions)

| Kategori | Score | Vurdering |
|---|---|---|
| **Offline** | **4.00** | Stærk – fastholder fejlsøgningskontekst |
| Regning | 3.83 | God – følger faktureringsspørgsmål |
| Hastighed | 3.80 | God – husker tekniske detaljer |
| Flytning/overdragelse | 3.80 | God – men fejler ved specifik eskalering |
| Etablering | 3.60 | OK – gentager sig ved leveringstids-spørgsmål |
| SBBU | 3.00 | Svag – taber salgskontext |
| Support øvrige | 2.60 | Kritisk – mister teknisk tråd |
| Ustabil | 2.40 | Kritisk – looper i generisk fejlsøgning |
| Øvrige | 2.33 | Kritisk – forstår ikke produktskifte |
| Udstyr | 2.20 | Kritisk – glemmer kundens situation |
| **SAMLET** | **3.19** | |

---

## 3. Dead Link Audit

**5 unikke døde links verificeret.** 6 sessions berørt.

| Link | Status | Kategori | Effekt |
|---|---|---|---|
| `https://www.hiper.dk/hjaelp/internet-og-wifi/offline` | **DEAD** (200 men forkert indhold) | Offline | ⛔ Kritisk – kunde med nedbrud sendes til død side |
| `https://www.hiper.dk/hjaelp/mit-abonnement/opsigelse` | **DEAD** | SBBU | ⛔ Kritisk – opsigelsesside utilgængelig |
| `https://www.hiper.dk/hjaelp/udstyr/bridgemode` | **DEAD** (200 men forkert) | Support øvrige | ⚠️ Moderat – teknisk guide utilgængelig |
| `https://www.hiper.dk/hjaelp/udstyr/bridge-mode` | **DEAD** (200 men forkert) | Support øvrige | ⚠️ Moderat – duplikat af ovenstående |
| `https://www.hiper.dk/hjaelp/internet-og-wifi/forskel-paa-signal-frekvenser` | **DEAD** (200 men forkert) | Ustabil | ⚠️ Moderat – WiFi-guide utilgængelig |

**Fungerende links (6 stk):**

| Link | Status |
|---|---|
| `https://drift.hiper.dk` | ✅ OK |
| `https://www.hiper.dk` | ✅ OK |
| `https://www.hiper.dk/mit-hiper/` | ✅ OK |
| `https://www.hiper.dk/hjaelp/internet-og-wifi/opsaetning-og-guides/bridge-mode` | ✅ OK |
| `https://www.hiper.dk/hjaelp/internet-og-wifi/fejlsoegning/ustabilt-internet` | ✅ OK |
| `https://www.hiper.dk/hjaelp/internet-og-wifi/opsaetning-og-guides/installationsmanual` | ✅ OK |

**Bemærk:** `perf.hiper.dk` (VLAN-tagging link fra v1) optræder ikke i denne kørsel.

---

## 4. Handover-rapport

### Overordnet fordeling (103 sessions)

| Status | Antal | Andel |
|---|---|---|
| **unnecessary** (bot svarede selv – OK) | 58 | 56% |
| **no** (manglende handover) | 22 | 21% |
| **yes** (korrekt handover) | 21 | 20% |
| **n/a** | 2 | 2% |

### Manglende handovers – kritisk (22 sessions)

| Kategori | Manglende | Kommentar |
|---|---|---|
| **Flytning/overdragelse** | **9 af 10** | Alle SALES_HANDOVER_EXPECTED – botten besvarer selv i stedet for at eskalere |
| **SBBU** | **7 af 12** | Salgsdialog uden eskalering til agent |
| **Regning** | 3 af 12 | Kunde kræver specificeret regning – botten kan ikke levere |
| **Øvrige** | 2 af 9 | Produktskifte kræver salgskontakt |
| **Offline** | 1 af 10 | Kunde har fulgt alt – bør eskaleres til tekniker |

**Kerneproblemet:** Flytning og SBBU er markeret `SALES_HANDOVER_EXPECTED`, men botten besvarer selv 16 af 22 cases. Botten er for "hjælpsom" – den burde eskalere til salg i stedet for at give generelle svar.

---

## 5. GPT5.0 Upgrade-anbefaling

**24 af 103 sessions (23%) er GPT5-kandidater.**

| Kategori | Kandidater | Andel | Hovedårsag |
|---|---|---|---|
| Regning | 6 | 50% | Konteksttab ved detaljerede faktureringsspørgsmål |
| Offline | 5 | 50% | Manglende eskaleringslogik |
| Hastighed | 3 | 30% | Gentager afviste løsninger |
| SBBU | 3 | 25% | Mister salgskontekst |
| Flytning | 2 | 20% | Mangler præcision ved opfølgning |
| Udstyr | 2 | 20% | Glemmer kundens specifik situation |
| Ustabil | 1 | 10% | Looper i generisk fejlsøgning |
| Etablering | 1 | 10% | Gentager svar |
| Øvrige | 1 | 11% | Off-topic svar |

### Anbefaling

**KB-forbedringer først, GPT5.0 derefter.** Estimeret fordeling af de 24 kandidater:

- ~14 sessions: Løses med KB-opdateringer alene (manglende viden, ikke modelfejl)
- ~6 sessions: Løses med GPT5.0's bedre konteksthukommelse
- ~4 sessions: Kræver både KB og model-opgradering

---

## 6. Systematisk Turn 2-fejl

**Alle 54 multi-turn sessions har tomme bot-svar i turn 2.** Dette er en scraper/session-resumption-fejl, ikke en Cognigy-fejl.

Mulige årsager:
- `cognigyWebChat.setCognigySessionId()` (Option B) virker ikke som forventet
- Session-cookie nulstilles mellem turns
- Welcome-besked fra ny session fanges i stedet for faktisk svar

**Impact:** Turn 2-spørgsmålene (ofte de mest relevante opfølgninger) får intet svar. Botten svarer først igen i turn 3-4, men uden kontekst fra turn 2.

**Anbefaling:** Debug session-resumption i `phase3_followup.js`. Test med `--limit 1` og log WebSocket-trafik.

---

## 7. Top 10 KB-huller (prioriteret)

### P1 – Kritisk (fix nu)

| # | Handling | Kategorier | Impact |
|---|---|---|---|
| 1 | **Fix 5 døde links** – offline, opsigelse, bridgemode (x2), signal-frekvenser | Offline, SBBU, Support, Ustabil | 6 sessions |
| 2 | **Tilføj eskaleringstrigger for SALES_HANDOVER_EXPECTED** – botten skal eskalere, ikke selvbesvare | Flytning, SBBU | 16 sessions |
| 3 | **Tilføj eskaleringsprocedure efter udtømt fejlsøgning** – "Kunde har prøvet alt → tilbyd tekniker (699 kr)" | Hastighed, Offline, Ustabil | 8 sessions |

### P2 – Vigtig (inden næste sprint)

| # | Handling | Kategorier | Impact |
|---|---|---|---|
| 4 | Tilføj produktskifte-FAQ (bredbånd ↔ 5G): pris, tilgængelighed, bindingsperiode | Øvrige | 4 sessions |
| 5 | Tilføj streaming- og tidsbaseret fejlsøgning (peak hours, QoS) | Ustabil | 5 sessions |
| 6 | Tilføj fuldmagtsformular-vejledning (hvor, hvordan, hvad hvis den mangler) | SBBU | 4 sessions |
| 7 | Tilføj betalingsalternativer (faktura, MobilePay, kortopdatering) | Regning | 3 sessions |
| 8 | Tilføj CGNAT/statisk IP/DynDNS dokumentation | Support øvrige | 3 sessions |

### P3 – Nice to have

| # | Handling | Kategorier | Impact |
|---|---|---|---|
| 9 | Tilføj leveringstider (fiber: 2-4 uger, 5G: 3-5 dage, kabel: 1-2 uger) | Etablering | 3 sessions |
| 10 | Tilføj udstyr-retursending FAQ (pris, emballage, frist, PostNord-tracking) | Udstyr | 3 sessions |
| 11 | Tilføj overdragelse ved dødsfald – fakturering og proces | Flytning | 1 session |
| 12 | **Reducer "Godt spørgsmål! 😊"** – max 1x per session, varier åbning | Alle | 70%+ af svar |

---

## 8. Systemfejl og observationer

### Tomme bot-svar (60 stk)
54 forekommer i turn 2 (systematisk). 6 forekommer i turn 3-4 (sporadisk):
- 2 sessions i Øvrige har helt tomme turn 3 – sessions er trunkeret/afbrudt
- 4 sessions har tomme turn 4-svar på specifikke opfølgninger

### Handover-markering
Kun 1 bot-besked har `handover=1` i hele datasættet, men mange svar indeholder tekst som "Jeg sender dig videre til en kollega." `HANDOVER_TEXT_MARKERS` i config.js fanger ikke disse. **Anbefaling:** Tilføj markørerne `'sender dig videre'`, `'kollega'`, `'medarbejder'`, `'du vil høre fra os'`.

### "Godt spørgsmål! 😊" overdosis
Optræder i 70%+ af alle bot-svar. Virker mekanisk og reducerer autenticitet. Master prompt bør varieres.

---

## 9. Sammenligning v1 → v2

| Metrik | v1 (25. feb) | v2 (26. feb) | Ændring |
|---|---|---|---|
| Sessions | 54 | 103 | +91% |
| Max turns | 3 | 4 | +1 turn |
| Rækker | 294 | 402 | +37% |
| Resolution (samlet) | 3.15 | 3.23 | +0.08 |
| Kontekstforståelse | 3.31 | 3.19 | -0.12 |
| GPT5-kandidater | 39% | 23% | -16pp |
| Dead links | Ikke verificeret | 5 verificeret | Ny data |
| Manglende handovers | 12 | 22 | +83% |
| Tomme bot-svar | 1 | 60 | Systematisk T2-bug |

**Bemærk:** Resolution steg marginalt, men manglende handovers steg kraftigt. Den største gevinst i v2 er dead link-verifikation og de 49 ekstra single-turn sessions der giver et bredere billede.

---

## Næste skridt

1. **Mikkel (P1):** Fix 5 døde links i KB (offline, opsigelse, bridgemode x2, signal-frekvenser)
2. **Mikkel (P1):** Implementér handover-trigger for SALES_HANDOVER_EXPECTED-kategorier
3. **Søren:** Debug Turn 2 session-resumption bug i `phase3_followup.js`
4. **Søren:** Udvid `HANDOVER_TEXT_MARKERS` med 'sender dig videre', 'kollega', 'medarbejder'
5. **Alle:** Kør v3 efter KB-rettelser og Turn 2-fix
6. **GPT5.0:** Afvent v3-resultater – evaluer derefter de resterende ~10 GPT5-kandidater
