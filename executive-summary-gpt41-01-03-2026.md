# Executive Summary – HiBot GPT-4.1 Kørsel, 1. marts 2026

**Kørsel:** `e4280789` · Endpoint: `gpt41` · 49 sessioner · 304 samtaletrin · 18:25–18:30

---

## Overordnet billede

Botten håndterer knap halvdelen af sessionerne selvstændigt (23/49 = 47%) og eskalerer til handover i 53% af tilfældene (26/49). Det er en høj handoverrate, men det interessante er *hvad der sker inden for de 26 handovers*: kun 8 er reelt berettigede. De øvrige 18 er enten "ingen kollegaer online" (11) eller "udenfor åbningstid" (5+2 overlap) – altså tidsstyrede afvisninger, ikke fagligt begrundede eskaleringer.

**Problemet er ikke primært GPT-4.1. Det er timingen af hvornår testen kørte (18:25–18:30, efter lukketid) kombineret med at botten falder tilbage til en templatebesked i stedet for at forsøge at besvare spørgsmålet.**

---

## Hvad sker der, når handover ikke kan gennemføres?

Botten følger ét fast mønster: den leverer en (relativt) nyttig svarbesked, *forsøger* at eskalere, men møder lukkede linjer og returnerer:

> *"Mine kollegaer er ikke online lige nu, da du har henvendt dig uden for åbningstiden"*

Herefter afsluttes samtalen. Ingen alternativ selvbetjening, ingen vidensartikler, ingen konkret hjælp. Det er det kritiske problem.

De **5 sessioner der burde have fået svar men ikke gjorde**, er alle spørgsmål botten *kunne have besvaret* med eksisterende KB-indhold:

| Kategori | Spørgsmål | Problem |
|---|---|---|
| Hastighed | WiFi 1000mbit – hvad er max hastighed? | Rent FAQ, intet handover-behov |
| Etablering | Fiber stik installation | Trin-for-trin guides tilgængeligt i KB |
| Øvrige | Skifte bredbånd → 5G | Produktinfo, tilgængeligt |
| Support øvrige | CGNAT / NAT-type (T3 cutoff) | Teknisk FAQ, svaret i KB |
| Regning | Første faktura – dobbeltbetaling? | Standard onboarding-spørgsmål |

**Fælles mønster:** Botten initierer handover uden tilstrækkelig selvhjælp-forsøg, og når agenter er offline, falder den til "lukket"-templatesvaret i stedet for at *udnytte at spørgsmålet faktisk er selvbetjeningsdueligt*.

---

## Hvad peger på masterprompt, KB eller model?

### Masterprompt-problem (sandsynligt)

Handover-tærsklen er for lav. Botten eskalerer tidligt – endda på rene FAQ-spørgsmål. Det tyder på at masterpromptens definition af *hvornår man skal eskalere* er for bred, eller at botten mangler en explicit instruktion om at *forsøge fuldstændigt selvbetjeningssvar før eskalering*. Særligt tydeligt i Hastighed og Support øvrige, hvor botten bør kunne svare fuldt ud.

Derudover mangler der tilsyneladende en "offline fallback"-logik i flowet: botten har ingen alternativ sti når handover-noden returnerer "agent unavailable". Den terminerer samtalen med en templatebesked, i stedet for at fortsætte med selvbetjeningssvar.

### KB-problem (bekræftet via dead links)

8 unikke dead links optræder stadig i svar – links som botten aktivt anbefaler, men som giver 404:

| URL | Forekomster |
|---|---|
| `/offline` | 3 |
| `/ustabil` | 2 |
| `/bridge-mode` | 2 |
| `/forskel-paa-signal-frekvenser` | 2 |
| `/hastighedstest` | 1 |
| `/bridgemode` | 1 |
| `/placering-af-router` | 1 |
| PDF-link (bredbåndsdækning) | 1 |

10 samtaleforløb sendes videre til en brudt ressource. KB'en indeholder stale links, og botten validerer dem ikke dynamisk. `/bridge-mode` vs. `/bridgemode` tyder på en URL-ændring der ikke er rullet igennem i indholdet. Dette er sandsynligvis ikke GPT-4.1's fejl – det er et KB-vedligeholdelsesproblem.

### Model (GPT-4.1) – begrænset evidens for model-specifikke fejl

Tekstlængden for svar med vs. uden handover er næsten identisk (386 vs. 370 tegn median) – botten varierer ikke sin udførlighed afhængigt af kompleksitet, hvilket tyder på at den ikke "mærker" svarsituationens sværhedsgrad. Det kan pege på at modellens kontekstudnyttelse er begrænset af promptstrukturen, ikke modellen i sig selv.

**Ingen hallucineringer identificeret i denne kørsel** (modsat session 11 i forrige rapport, der var kritisk – "Sopgave", "Arcde", "doubleuifai"). GPT-4.1 performer renere end forgængeren på faktuel FAQ-opgave.

---

## Nøgletal

| Metric | Værdi |
|---|---|
| Sessioner total | 49 |
| Handover-rate | 53% (26/49) |
| Reelt berettigede handovers | ~16% (8/49) |
| Blokeret af lukketid / ingen agenter | 33% (16/49) |
| Dead links i svar | 8 unikke URLs, 10 forekomster |
| Sessioner afsluttet ved T1 | 5 (bot stoppede med det samme) |
| Sessioner der nåede T4 | 27 (55%) |

### Handover-rate per kategori

| Kategori | Handover-rate |
|---|---|
| Regning | 83% |
| Flytning/overdragelse | 80% |
| Hastighed | 80% |
| Øvrige | 75% |
| Offline | 60% |
| Udstyr | 0% |
| Ustabil | 0% |
| Etablering | 0% |
| SBBU | 0% |
| Support øvrige | 0% |

---

## Top 3 anbefalinger

### 1. Indfør "selvbetjening-først"-logik i masterprompt

Botten bør have eksplicit instruktion: *Forsøg at besvare fuldt med KB-indhold. Eskalér kun hvis brugeren har behov for kontohandling, fejlfinding der kræver systemadgang, eller kompleksitet der overgår KB.* Det ville reducere unødvendige handovers markant og sikre at kunder udenfor åbningstid stadig får hjælp.

### 2. Implementér "offline fallback"-svar med konkret hjælp

Når agenter er offline, bør botten *ikke* bare sige "vi er lukket". Den bør:
- Levere det bedst mulige selvbetjeningssvar baseret på spørgsmålet
- Tilbyde at eskalere næste hverdag (med åbningstider)
- Pege på relevante selvbetjeningsressourcer

Cognigy understøtter dette via betingede flows på handover-noden (`is_agent_available` condition).

### 3. Fix dead links i KB (akut)

Alle 8 dead links bør enten opdateres til korrekte URLs eller fjernes fra KB-artiklerne. Dette er en hurtig gevinst med direkte brugerimpact – 10 samtaler i denne kørsel alene sendte brugeren til en 404-side.

Prioriter: `/offline`, `/bridge-mode`/`/bridgemode` (URL-inkonsistens), `/ustabil`, `/forskel-paa-signal-frekvenser`.

---

*Rapport genereret: 1. marts 2026 · Datagrundlag: conversations-gpt41-19.30-01-03-2026.csv*
