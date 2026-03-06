# HiBot Scraper – Status til Alexander, 5. marts 2026

Vi har bygget et automatiseret test-framework (Playwright + SQLite) der kører 49 strukturerede kundesimuleringer mod Cognigy-chatten i parallelle sessioner. Hvert scenarie stiller et realistisk spørgsmål (turn 1) + 2-3 naturlige opfølgere. Resultaterne scores, dead links verificeres, og alt gemmes til analyse. Ideen er: lave ændringer i Cognigy, trykke på knappen, og se om det faktisk blev bedre.

---

## Hvad vi har fundet

**Baseline (v2, 26. feb):** Botten scorede 3.23/5 på resolution og 3.19/5 på kontekstforståelse over 103 sessioner. Stærkest på Flytning og Etablering (~4.0), svagest på Ustabil og Øvrige (~2.0). En kritisk bug opdaget: alle turn 2-svar var tomme pga. en session-resumption-fejl i scraperen. Fixet inden næste kørsel.

**Efter prompt- og KB-justeringer (v6, 27. feb):** Resolution op til 3.67/5. Kontekstforståelse hele vejen op til 4.58/5. Andel af sessioner der var "så dårlige at de burde have brugt GPT-5" faldt fra 23% til 12%. Det er en tydelig og målbar forbedring på én dag.

**GPT-5-testen (26. feb):** Vi kørte de samme 49 scenarier mod GPT-5-endpoint. Observerbar hallucination i mindst én session – botten genererede meningsløst garblede svar ("Sopgave", "Arcde", "doubleuifai"). GPT-4.1 viste ikke dette i samme kørsler. Ingen grund til at skifte model pt.

**Seneste kørsel (1. marts, kl. 18:25):** 49 sessioner, GPT-4.1. Handover-rate: 53% (26/49), men kun 8 af dem er reelt berettigede. 16 handovers var tidsstyrede afvisninger fordi kørslen skete efter lukketid – botten møder "ingen agenter online" og svarer bare "vi er lukket" i stedet for at besvare spørgsmålet. 5 af disse sessioner var rene FAQ-spørgsmål som burde kunne besvares uden menneskelig agent overhovedet.

---

## Vidensdatabasen – huller og dead links

Svage kategorier på tværs af alle kørsler: *Ustabil* (streaming-fejl, signalproblemer) og *Øvrige* (produktskifte, bredbånd→5G, CGNAT). Botten looper i generisk fejlsøgning og kan ikke vejlede konkret.

Dead links er et persisterende problem. På tværs af kørsler ser vi disse URLs dukke op gentagne gange i svar – men de giver 404:

`/offline`, `/ustabil`, `/bridge-mode` + `/bridgemode` (to varianter af samme side!), `/forskel-paa-signal-frekvenser`, `/hastighedstest`, `/placering-af-router`

Det er ikke GPT-4.1's fejl – det er KB-indhold der peger på forældede URLs. Hurtig gevinst at fixe.

---

## Hvad "hack-n-slash"-simuleringerne er værd

Den store indsigt er at vi nu kan kvantificere effekten af ændringer. Vi har allerede set: prompt-justering + KB-opdatering → +0.44 point resolution på én dag. Det er ikke noget man ville vide uden simuleringer. Vi fandt også T2-buggen, dead links og hallucinationen i GPT-5 – alle ting der i produktion ville have ramt rigtige kunder i månedsvis uden opdagelse.

Næste step er at bygge et continuous loop: kør simuleringer, identificer svage punkter, lav ændringer i Cognigy, kør igen, mål delta. Vi har infrastrukturen til det nu.

---

*Detaljer: rapport-del1.md (sessioner 1–25), rapport-del2.md (sessioner 26–49), rapport-v2.md (baseline), rapport-v6.md (efter forbedringer), executive-summary-gpt41-01-03-2026.md (seneste kørsel)*
