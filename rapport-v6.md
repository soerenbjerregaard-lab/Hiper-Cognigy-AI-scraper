# Rapport v6 – Hiper Cognigy AI Chatbot
**Kørselsdato:** 27. februar 2026, kl. 06:52–06:57
**Endpoint:** gpt41
**Run ID:** 76aba6cd-242b-498a-ae9a-ef0121118445
**Scenarier:** 49 sessioner | 4 turns max | 280 rækker i DB
**Analyseret af:** Claude Sonnet 4.6, 27. feb 2026

---

## Executive Summary

Kørsel v6 viser en **markant forbedring** ift. tidligere kørsler. Den gennemsnitlige løsningskvalitet er steget til **3.67/5** (mod 3.23 i v2-baseline med 103 sessioner). Kontekstforståelse over flere turns er fremragende med **4.58/5** i gennemsnit. Antallet af GPT-5 kandidater er faldet fra 23% til **12%** (6/49 sessioner).

De største resterende problemer er:
1. **5 unødvendige handovers** — botten eskalerer for simple spørgsmål der burde besvares direkte
2. **4 dead links** der fortsat ikke er fixede (persisterende fra v3–v5)
3. **4 vidensgab** med primært manglende produkt- og procesinfo

Kritisk svage kategorier er nu kun **Øvrige (2.75)** og **Etablering (3.2)**.

---

## Run-metadata

| Metric | Værdi |
|--------|-------|
| Sessioner | 49 |
| Turns samlet | T1: 49 / T2: 40 / T3: 29 / T4: 22 |
| Fejl (ERROR) | 0 ✅ |
| Tomme bot-svar | 0 ✅ |
| Handover rate | 30/49 = 61% |
| Unødvendige handovers | 5 |
| Dead link-sessioner | 6 (4 unikke URLs) |
| GPT-5 kandidater | 6/49 = 12% |

---

## Per-kategori scorecard

| Kategori | Sessions | Avg Resolution | Handover rate | Unødv. HO | Dead links | KB-gap |
|----------|----------|---------------|---------------|-----------|------------|--------|
| Etablering | 5 | **3.2** | 60% (3/5) | 1 | — | — |
| Flytning/overdragelse | 5 | **3.4** | 100% (5/5) ✓ | 1 | — | Router-pris |
| Hastighed | 5 | **3.8** | 80% (4/5) | 1 | — | WiFi 6-router |
| Offline | 5 | **3.8** | 60% (3/5) | — | 2 sessions | — |
| Regning | 6 | **3.8** | 67% (4/6) | 1 | — | Oprettelses-gebyr |
| SBBU | 4 | **3.8** | 50% (2/4) ✓ | — | — | Fuldmagt-placering |
| Support øvrige | 5 | **4.2** | 40% (2/5) | — | 1 session | DynDNS/statisk IP |
| Udstyr | 5 | **4.2** | 40% (2/5) | — | — | — |
| Ustabil | 5 | **3.6** | 40% (2/5) | — | 3 sessions | — |
| Øvrige | 4 | **2.8** | 75% (3/4) | 1 | — | 5G-skift, pris ved overdragelse |
| **TOTAL** | **49** | **3.67** | **61% (30/49)** | **5** | **6 sessions** | **5 gaps** |

*✓ = SALES_HANDOVER_EXPECTED, handovers er forventede*

---

## Detaljeret kategori-analyse

### Etablering (3.2/5)

**Stærke sessioner:**
- `8f821e3b` (4t, 5/5): Ren, informativ session om fiber/5G/coax etablering uden tekniker. Korrekte detaljer om 699 kr teknikerbesøg.
- `f66478c2` (4t, 5/5): God om fiberboks, automatisk teknikerbesøg vs. Mit Hiper, 699 kr pris.

**Svage sessioner:**
- `cf9159a7` (1t, 0/5 ❌): Bruger spørger "vi har ikke noget stik i huset, hvordan fungerer det?" — bot eskalerer **straks** til handover uden at svare. Dette er et basalt præ-salgs spørgsmål der burde besvares.
- `d53ad310` (2t, 3/5): T1 om fiberboks-udskiftning er ok men vag. T2 om hvem der betaler er endnu vagere — botten siger "som udgangspunkt ikke dig, men der kan være undtagelser" og eskalerer. Kunden fortjener et klarere svar.

**Gennemgående god:** botten kender 699 kr teknikerbesøg-pris, Mit Hiper-links, og fiber vs. coax-distinktionen.

---

### Flytning/overdragelse (3.4/5)

Alle handovers er forventede (SALES_HANDOVER_EXPECTED).

**Stærke sessioner:**
- `3b9012ec` (1t, 5/5): Dødsfald-overdragelse → øjeblikkelig, empatisk handover. Korrekt adfærd.
- `0e48bcaf` (3t, 4/5): God om flytningsprocedure via mail, Mit Hiper, og dato-logik.

**Svage sessioner:**
- `82515605` (2t, 2/5 ❌): T1 om router ved flytning er god. T2 "hvad koster ny router?" → øjeblikkelig handover-kø uden svar. **Botten burde kende router-priser** eller i det mindste sige "tjek hiper.dk/udstyr".
- `21cc5802` (2t, 3/5): T2 om teknikerbesøg-pris ved ny adresse giver et upræcist "699 kr forgæves" svar, som er forkert kontekst (det er jo installation, ikke forgæves besøg).

**KB-gap:** Router-pris ved skift af forbindelsestype.

---

### Hastighed (3.8/5)

**Stærke sessioner:**
- `382f3c4d` (3t, 4/5): Fremragende teknisk fejlsøgning — CAT5e/CAT6, gigabit NIC, VPN-deaktivering. Handover ved T3 (linje-tjek) er korrekt.
- `85e77e70` (3t, 4/5): God om router-krav (gigabit LAN, NIC). T3 handover om lånerouter er borderline men ok.
- `9126b6d4` (3t, 4/5): Stærk. Botten erkender selv "jeg kan ikke se live-status" — self-awareness er god.
- `d0a02ca8` (4t, 5/5): Perfekt progression fra type-spørgsmål → fejlsøgning → reset → hastighedsgaranti-forklaring.

**Svage sessioner:**
- `92434111` (2t, 2/5 ❌): T1 om WiFi-begrænsning er fremragende. T2 "kan jeg købe en bedre Hiper-router med WiFi 6?" → handover-kø. **Dette er et simpelt produktspørgsmål.** Botten burde enten svare ja/nej eller linke til udstyrssiden.

**KB-gap:** WiFi 6-router tilgængelighed i Hipers sortiment.

---

### Offline (3.8/5)

**Stærke sessioner:**
- `7e7c7c40` (1t, 4/5): Bruger siger "jeg har fulgt alle anvisninger" → botten eskalerer korrekt til fejlmelding via Mit Hiper.
- `d160e001` (4t, 4/5): God progression — spørger om type, fiberboks alle lys slukket = strømproblem, korrekt diagnose.
- `f9a7c157` (4t, 4/5): Korrekt rækkefølge: reset → Mit Hiper fejlmelding → drift.hiper.dk → teknikerbesøg via handover.

**Svage sessioner:**
- `06ab3b7c` (4t, 3/5): T3 og T4 gentager de samme trin (kabel, reset) selvom brugeren allerede har gjort det. Botten burde have eskaleret til fejlmelding efter T2-reset uden effekt. **Manglende 2-turn escape hatch.**

**Dead links (2 sessioner):**
- `06ab3b7c` og `d160e001`: Begge refererer til `https://www.hiper.dk/hjaelp/internet-og-wifi/offline` (404). Kritisk link der nævnes direkte i fejlsøgningssvar.

---

### Regning (3.8/5)

**Stærke sessioner:**
- `1c6a3f03` (4t, 5/5): Korrekt og klar om første-regning-logik (2 måneder), Mit Hiper-overblik, ingen faktura, 2 rykkergebyrer.
- `4f744f92` (4t, 5/5): God om kortskift, fejlfinding, ingen MobilePay, rykkergebyr-logik.

**Svage sessioner:**
- `f9f12de6` (2t, 2/5 ❌): T1 om første regning er fin. T2 "hvad koster oprettelsen præcist? Det fremgår ikke klart" → øjeblikkelig handover. **Botten burde kende oprettelsesgebyret** (eller et interval). Dette er en meget hyppig kundespørgsmål.
- `55dceb16` (1t, 3/5): Botten giver en god forklaring om første-regning-logik OG triggerer handover i samme svar. Handoveren virker automatisk snarere end situationsbestemt — brugeren spurgte om dobbeltbetaling, botten svarede men eskalerede alligevel.

**KB-gap:** Præcist oprettelsesgebyr (beløb).

---

### SBBU (3.8/5)

**Stærke sessioner:**
- `5d4522d5` (4t, 5/5): Fremragende — korrekt om fuldmagt via Mit Hiper, at Hiper IKKE automatisk overholder opsigelsesvarsel (brugeren skal selv angive dato), hvad sker der hvis Yousee afviser.
- `8c562865` (4t, 5/5): Korrekt om 30-dages frist for fuldmagt ⚠️ (se hallucination-note), chat-support, opsigelsesvarsel.

**Svage sessioner:**
- `4cdea469` (1t, 3/5): Nævner korrekt at fuldmagt kræves, men eskalerer uden at give yderligere info.
- `f8bb9ebc` (2t, 2/5): T2 "jeg kan ikke finde fuldmagten i Mit Hiper, hvor er den præcist?" → botten indrømmer "det er ikke præcist beskrevet" og tilbyder handover. **KB-gap: præcis placering af fuldmagt-funktionen i Mit Hiper.**

---

### Support øvrige (4.2/5)

Bedste kategori i denne kørsel. Tekniske svar er generelt præcise og dybe.

**Stærke sessioner:**
- `a5e1a8ca` (4t, 5/5): Perfekt om ethernet-kabler — korrekt om CAT5e vs CAT6 vs CAT7, 100m max, afskærmning irrelevant i hjemmet.
- `c55dce89` (4t, 5/5): God om WiFi-dækning i betonhus, mesh til 19 kr/enhed, ingen teknikerbesøg til WiFi-opt.
- `996dd39a` (4t, 4/5 ⚠️): Teknisk set gode svar om mesh/bridge mode — men alle 4 turns indeholder **dead link** til `/bridge-mode`.

**Svage sessioner:**
- `cabc1c4c` (4t, 3/5): T3 "understøtter Hipers router DynDNS?" → ærlig KB-gap svar ("ikke nævnt i vores vejledninger"). T4 statisk IP → handover. Ærlig og korrekt håndtering af manglende viden, men **KB-gap er reel og burde lukkes**.

**Dead link (1 session, 4 turns):**
- `996dd39a`: `https://www.hiper.dk/hjaelp/udstyr/bridge-mode` (404) — kritisk teknisk guide.

---

### Udstyr (4.2/5)

Næstbedste kategori. Konkrete, faktuelle svar om retur-logistik.

**Stærke sessioner:**
- `87a12c0e` (4t, 5/5): Korrekt returadresse (Hiper A/S, C/o MatKon, Måløv Byvej 229, 2760 Måløv), 34-dages frist, 99 kr rykkerbrev + 599 kr ikke-returneret gebyr.
- `f16191e7` (4t, 5/5): God om omdeling vs. pakkeshop-retur, frister, ansvarsfordeling.

**Svage sessioner:**
- `0348025e` (1t, 3/5): Handover for "mangler 1 ud af 3 routere" er korrekt men botten bruger ikke chancen for at forklare gebyr-strukturen.
- `b06c1df2` (4t, 4/5): T3 "hvad sker der hvis pakken returneres?" → vagt svar ("skriv til os"). Burde have nævnt at de genleverer.

---

### Ustabil (3.6/5)

**Stærke sessioner:**
- `16550600` (4t, 4/5): Korrekt at fiber ikke kan prioriteres til streaming, drift.hiper.dk link.
- `5021f2f3` (4t, 4/5): God fejlsøgning, MIT Hiper WiFi signal-tjek nævnt.
- `fe5b9067` (4t, 4/5): God eskalation efter udtømt fejlsøgning — "dagligt problem, træt af det" → handover til tekniker.

**Svage sessioner:**
- `ea4f3a5e` (4t, 3/5): T3 om aftenes-problemer → "kan skyldes mange ting, ikke noget i vores vejledninger om belastning". Ærlig, men botten tilbyder ingen escalation eller konklusion i T4 — bare "fejlmeld via Mit Hiper" endnu en gang.
- `f76d9c24` (3t, 3/5): T3 om 18-20 belastning → korrekt at fiber burde klare det, men handover uden bedre resolution.

**Dead links (3 sessioner):**
- `ea4f3a5e` + `fe5b9067`: `/forskel-paa-signal-frekvenser` (404) — nævnt i T2
- `f76d9c24`: `/ustabil` (404) — nævnt i T2

---

### Øvrige (2.8/5)

Svageste kategori. To ud af fire sessioner håndteres dårligt.

**Stærke sessioner:**
- `b55e2498` (4t, 4/5): God om profilændring i Mit Hiper, lidt repetitiv men korrekt.
- `aa565ee5` (2t, 4/5): Korrekt — "email i brug" kræver manuel håndtering, handover.

**Svage sessioner:**
- `fa5b6657` (1t, 0/5 ❌): "Kan jeg skifte fra bredbånd til 5G?" → **øjeblikkelig handover-kø**. Dette er et basalt produktspørgsmål. Botten burde beskrive processen (opsig bredbånd, bestil 5G). **Hårdeste unødvendige handover i hele kørslen.**
- `678c0c2b` (3t, 3/5): T1-T2 om arbejdsgiver-betalt abonnement er gode. T3 "ændres prisen?" → "kan ikke oplyse, sender videre". **KB-gap: pris ved overdragelse fra arbejdsgiver til privat.**

---

## Handover audit

### Unødvendige handovers (5 stk.)

| Session | Kategori | Turn | Spørgsmål | Problem |
|---------|----------|------|-----------|---------|
| `cf9159a7` | Etablering | T1 | "Vi har ikke noget stik i huset, hvordan fungerer det?" | Basis præ-salgs-info |
| `82515605` | Flytning | T2 | "Hvad koster det at få en ny router?" | Simpel produktpris-forespørgsel |
| `92434111` | Hastighed | T2 | "Kan jeg købe en bedre Hiper-router med WiFi 6?" | Simpel produktforespørgsel |
| `f9f12de6` | Regning | T2 | "Hvad koster oprettelsen præcist?" | Kendt fakta-svar |
| `fa5b6657` | Øvrige | T1 | "Kan jeg skifte fra bredbånd til 5G?" | Basis produktskifte-info |

**Fællestrækket:** Alle 5 eskalerer på faktuelle spørgsmål om priser, produkter eller basale processer. Botten mangler enten vidensbaser-indhold eller har for lav threshold for handover.

### Justerede handovers — noteworthy

- `3b9012ec` (dødsfald-overdragelse): øjeblikkelig handover uden tøven — korrekt og empatisk ✅
- `7e7c7c40` (fulgte alle instrukser): korrekt eskalation ✅
- `fe5b9067` (dagligt problem, træt): god frustrations-detektion → tekniker ✅

---

## Dead link audit

4 unikke dead URLs — **alle var kendte fra v3–v5. Ingen er fixet.**

| URL | HTTP Status | Berørte sessioner | Kategori | Alvorlighed |
|-----|------------|-------------------|----------|-------------|
| `/hjaelp/internet-og-wifi/offline` | 404 | 2 (06ab3b7c, d160e001) | Offline | 🔴 Kritisk |
| `/hjaelp/udstyr/bridge-mode` | 404 | 1 (996dd39a, alle 4 turns) | Support øvrige | 🔴 Kritisk |
| `/hjaelp/internet-og-wifi/ustabil` | 404 | 1 (f76d9c24) | Ustabil | 🟡 Medium |
| `/hjaelp/internet-og-wifi/forskel-paa-signal-frekvenser` | 404 | 2 (ea4f3a5e, fe5b9067) | Ustabil | 🟡 Medium |

De to kritiske links (`/offline` og `/bridge-mode`) er direkte svar-links der aktivt guider kunder til døde sider. **Bør fixes omgående i Cognigy knowledge base.**

---

## Vidensgab (KB gaps)

| Gap | Berørte sessioner | Effekt |
|-----|-------------------|--------|
| Fuldmagt-placering i Mit Hiper | `f8bb9ebc` (SBBU) | Unødvendig handover |
| Oprettelsesgebyr (præcist beløb) | `f9f12de6` (Regning) | Unødvendig handover |
| WiFi 6 router tilgængelighed | `92434111` (Hastighed) | Unødvendig handover |
| 5G-skift processen (fra fiber/coax) | `fa5b6657` (Øvrige) | Unødvendig handover |
| DynDNS support i Hiper-router | `cabc1c4c` (Support øvrige) | Svagt svar (acceptabelt) |

---

## Hallucination-risici

| Session | Påstand | Risiko | Kommentar |
|---------|---------|--------|-----------|
| `8c562865` | "30 dage efter opstart til at indsende fuldmagt" | ⚠️ Lav-medium | Præcis grænse ikke verificerbar fra offentligt materiale |
| `194545e4` | "NAT type 2 på fiber" | ✅ Lav | Teknisk korrekt for de fleste konfigurationer |
| `87a12c0e` | "34 dages returfrist" | ✅ Lav | Nævnes konsistent i to uafhængige sessioner, sandsynligvis korrekt |

**Overordnet hallucinations-niveau: lavt.** Ingen grove faktuelle fejl identificeret i denne kørsel.

---

## Multi-turn konteksthåndtering

Gennemsnitlig context retention (38 multi-turn sessioner): **4.58/5**

Dette er en markant forbedring fra v2-baseline (3.09 multi-turn). Botten husker i det store hele spørgsmålskontekst, bruger-type (fiber/coax/5G), og bygger naturligt videre på foregående turns.

**Eksempler på fremragende kontekst:**
- `d0a02ca8` (Hastighed, 4t): progression fra type-afklaring til fejlsøgning til hastighedsgaranti-forklaring
- `5d4522d5` (SBBU, 4t): fuldmagt, datoer, hvad sker der ved afvisning — holder tråden perfekt
- `87a12c0e` (Udstyr, 4t): retur-label → adresse → gebyrer → frist, konsekvent og korrekt

**Svagt kontekst-flow (ikke dårligt, men repetitivt):**
- `06ab3b7c` (Offline, 4t): gentager kabel-/reset-trin i T3+T4 selvom T2 allerede dækkede dem

---

## GPT-5 kandidater (resolution ≤ 2)

6 sessioner = **12%** (vs. 23% i v2 baseline)

| Session | Kategori | Resolution | Årsag |
|---------|----------|-----------|-------|
| `cf9159a7` | Etablering | 0 | Øjeblikkelig handover, intet svar |
| `fa5b6657` | Øvrige | 0 | Øjeblikkelig handover, intet svar |
| `82515605` | Flytning | 2 | Handover på simpel router-pris |
| `f9f12de6` | Regning | 2 | Handover på oprettelsesgebyr |
| `f8bb9ebc` | SBBU | 2 | KB-gap: fuldmagt-placering |
| `92434111` | Hastighed | 2 | Handover på WiFi 6-produkt |

---

## Sammenligning med tidligere versioner

| Metrik | v2 (baseline) | v6 (27. feb) | Ændring |
|--------|--------------|--------------|---------|
| Samlet resolution | 3.23 | **3.67** | +0.44 ✅ |
| Single-turn avg | 3.39 | ~3.5 | +0.1 ✅ |
| Multi-turn avg | 3.09 | ~3.7 | +0.6 ✅ |
| Context retention | ~3.5 | **4.58** | +1.1 ✅ |
| GPT-5 kandidater | 23% | **12%** | -11% ✅ |
| Dead links (unikke) | 5 | **4** | -1 ✅ |
| Ustabil avg | 2.10 | **3.6** | +1.5 ✅✅ |
| Øvrige avg | 2.00 | **2.8** | +0.8 ✅ |

**Ustabil og Øvrige er forbedret markant** — de to kategorier der var kritisk svage i v2.

---

## Anbefalinger

### Prioritet 1 — Fix dead links (ingen kode-ændring nødvendig)

Opret eller omdirigér disse 4 sider på hiper.dk:
- `/hjaelp/internet-og-wifi/offline` → Offline fejlsøgningsguide
- `/hjaelp/udstyr/bridge-mode` → Bridge mode opsætningsguide
- `/hjaelp/internet-og-wifi/ustabil` → Ustabil forbindelse guide
- `/hjaelp/internet-og-wifi/forskel-paa-signal-frekvenser` → Frekvens-guide

### Prioritet 2 — Luk de 4 KB-gaps (Cognigy knowledge base update)

1. **Oprettelsesgebyr:** Tilføj præcist beløb (eller interval) til knowledge base
2. **WiFi 6 router:** Beskriv hvilke Hiper-routere der understøtter WiFi 6 + salgspris/lejepris
3. **5G-skift:** Tilføj artikel om processen for at skifte fra fiber/coax til 5G mobilt bredbånd
4. **Fuldmagt-placering:** Beskriv præcist UI-sti i Mit Hiper (fx "Abonnement → Skift udbyder → Fuldmagt")

### Prioritet 3 — Reducer unødvendige handovers (Cognigy flow/prompt)

De 5 unødvendige handovers er alle på spørgsmål med svar der allerede burde findes i KB. Løsning:
- Tilføj router-priser til knowledge base (fix `82515605` + `92434111`)
- Tilføj proces for 5G-skift (fix `fa5b6657`)
- Sænk handover-threshold for basale produkt-forespørgsler

### Prioritet 4 — Verifér 30-dages fuldmagt-claim (8c562865)

Tjek om "30 dage efter opstart" for fuldmagt er et dokumenteret tal — ellers fjern påstanden fra KB.

### Prioritet 5 — 2-turn escape hatch i Offline

Session `06ab3b7c` viser at botten gentager reset-instrukser i T3+T4 selvom brugeren allerede har gjort det. Overvej regel: "Hvis brugeren nævner at reset ikke hjalp, gå direkte til Mit Hiper fejlmelding."

---

*Rapport genereret 27. februar 2026 af Claude Sonnet 4.6 på baggrund af 49 sessioner fra run `76aba6cd`.*
