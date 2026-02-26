# Hiper Cognigy AI Scraper

## Formål
At bygge en maskine, som kan trykteste Hipers AI-assisted Chatbot, som er drevet af Cognigy. Vi spammer botten med en masse spørgsmål, og gemmer svar i en DB, som så hentes ud af undertegnede og behandles manuelt.
Formålet er at løfte svarkvaliteten af botten.

## Arkitektur
- **Udvikling:** MacBook → denne mappe
- **Repo:** https://github.com/soerenbjerregaard-lab/Hiper-Cognigy-AI-scraper
- **Server:** Lenovo via Tailscale (100.124.174.76)
- **Database:** SQLite på serveren

## Deploy-flow (OBLIGATORISK)
1. Alle ændringer laves LOKALT i denne mappe
2. git add, commit, push til GitHub
3. SSH til Lenovo → git pull → genstart services
4. ALDRIG rediger filer direkte på serveren

## Regler
- Rediger ALDRIG filer direkte på serveren via SSH
- Alle kodeændringer sker lokalt og pushes via git
- SSH til serveren bruges KUN til: git pull, genstart services, tjek logs, database queries
- Bekræft git status før og efter arbejde
