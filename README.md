# Mattequiz

En enkel nettbasert matteapp der du øver på addisjon, subtraksjon, multiplikasjon og divisjon. Målet er å svare riktig på alle 20 spørsmål så fort som mulig.

## Funksjoner

- 20 tilfeldig genererte regnestykker per runde (tall 1–20)
- Tidtaking – beat your best time
- Ledertavle for perfekte runder (20/20), sortert på tid
- Profilside med graf over fremgang over tid
- Invitasjonslenker – nye brukere registrerer seg via en engangslenkke (ingen passord)
- Eksisterende brukere logger inn ved å skrive navnet sitt

## Tech stack

- **Backend:** Python / Flask
- **Database:** SQLite
- **Server:** Gunicorn
- **Deployment:** Docker + Docker Compose

---

## Oppsett på VPS

### Forutsetninger

- En VPS med Docker og Docker Compose installert
- Et domenenavn som peker mot VPS-en (nødvendig for HTTPS)

### 1. Klon repoet

```bash
git clone <repo-url> mattequiz
cd mattequiz
```

### 2. Opprett miljøvariabelfil

```bash
cp .env.example .env
```

Rediger `.env` og fyll inn verdiene:

```env
SECRET_KEY=<lang-tilfeldig-streng>
DB_PATH=/data/mattequiz.db
DOMAIN=dittdomene.no
BASE_URL=https://dittdomene.no
```

Generer en god `SECRET_KEY` med f.eks.:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Bygg og start

```bash
docker compose up -d --build
```

Caddy starter automatisk og henter SSL-sertifikat fra Let's Encrypt første gang. Appen er tilgjengelig på `https://dittdomene.no` etter noen sekunder. Sertifikater lagres i Docker-volumet `caddy_data` og fornyes automatisk. Databasen lagres i `./data/` på hosten og overlever container-restart.

### 4. Inviter brukere

Generer en invitasjonslenke (engangslenkke):

```bash
docker compose exec app python manage.py generate-token
```

Eksempelutput:

```
https://dittdomene.no/register/550e8400-e29b-41d4-a716-446655440000
```

Send lenken til brukeren. Brukeren skriver inn fornavnet sitt og er klar til å spille. Lenken kan bare brukes én gang.

### 5. Eksisterende brukere

Brukere som allerede er registrert kan logge inn direkte på forsiden ved å skrive inn navnet sitt – ingen ny invitasjonslenke trengs.

---

## Daglig drift

| Oppgave | Kommando |
|---------|----------|
| Se logger | `docker compose logs -f` |
| Restart | `docker compose restart` |
| Stopp | `docker compose down` |
| Oppdater til ny versjon | `git pull && docker compose up -d --build` |
| Generer ny invitasjonslenke | `docker compose exec app python manage.py generate-token` |

Databasefilen ligger på hosten i `./data/mattequiz.db` og sikkerhetskopieres ikke automatisk. Ta gjerne jevnlige sikkerhetskopier:

```bash
cp data/mattequiz.db data/mattequiz.db.bak
```
