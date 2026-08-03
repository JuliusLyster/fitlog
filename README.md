# FitLog - Personlig Fitness & Ernæringsanalyse

FitLog er en webapplikation hvor brugeren dagligt kan logge sine måltider
og træningspas, og få et klart overblik over kalorie- og makronæringsindtag
(protein, kulhydrat, fedt) samt træningsaktivitet over tid. Appen giver
desuden personlige AI-genererede anbefalinger baseret på de loggede data.

## Indhold

- [Arkitektur](#arkitektur)
- [Kom i gang](#kom-i-gang)
- [Brug af appen](#brug-af-appen)
- [API-eksempler](#api-eksempler-curlhttpie)
- [Tests og kodekvalitet](#tests-og-kodekvalitet)
- [Projektstruktur](#projektstruktur)
- [Arkitekturvalg (til mundtligt forsvar)](#arkitekturvalg-til-mundtligt-forsvar)

## Arkitektur

```
┌─────────────┐      HTTP/JSON      ┌─────────────┐      HTTP       ┌─────────────┐
│  Streamlit  │ ──────────────────► │   FastAPI   │ ───────────────► │   Ollama    │
│  (frontend) │ ◄────────────────── │  (backend)  │ ◄─────────────── │  (lokal LLM)│
└─────────────┘                     └──────┬──────┘                 └─────────────┘
                                            │
                                            │ SQLAlchemy
                                            ▼
                                     ┌─────────────┐        HTTP       ┌──────────────────┐
                                     │   SQLite    │        ────────►  │ Open Food Facts   │
                                     │  (volume)   │                    │      (API)        │
                                     └─────────────┘                    └──────────────────┘
```

Tre services orkestreret med Docker Compose:

1. **backend** (FastAPI) - REST API med CRUD for brugere, måltider og
   træningspas. Beregner makroer via Open Food Facts, aggregerer data med
   Pandas/NumPy, og henter AI-anbefalinger fra Ollama.
2. **frontend** (Streamlit) - Formularer til logning og et dashboard med
   grafer. Taler udelukkende med backendens REST API - aldrig direkte med
   databasen.
3. **ollama** - Kører en lokal LLM (standard: `llama3`) som backend spørger
   om personlige anbefalinger.

## Kom i gang

### Forudsætninger

- Docker og Docker Compose installeret

### Opsætning

1. Klon/udpak projektet, og gå til projektroden:

   ```bash
   cd fitlog
   ```

2. Kopiér miljøvariabel-eksemplet:

   ```bash
   cp .env.example .env
   ```

3. Start alle services:

   ```bash
   docker compose up --build
   ```

4. Første gang skal Ollama-modellen hentes ned (kun nødvendigt én gang):

   ```bash
   docker exec fitlog-ollama ollama pull llama3
   ```

5. Åbn appen:

   - Frontend (Streamlit): http://localhost:8501
   - Backend API-dokumentation (Swagger): http://localhost:8000/docs

### Stoppe appen

```bash
docker compose down
```

Data i SQLite-databasen og Ollama-modellen ligger i navngivne Docker-volumes
(`fitlog-data` og `ollama-data`) og overlever altså `docker compose down`.
Brug `docker compose down -v` for også at slette data.

### Skifte LLM-udbyder til Mistral

Sæt i `.env`:

```
LLM_PROVIDER=mistral
MISTRAL_API_KEY=din-api-nøgle-her
```

og genstart med `docker compose up --build`. Ollama-servicen behøver ikke
engang køre i så fald.

## Brug af appen

1. Gå til **Forside** og opret en bruger med navn og vægt (bruges til at
   beregne forbrændte kalorier), eller vælg en eksisterende bruger.
2. Under **Log Måltid**: skriv en fødevare og en mængde i gram. Appen
   beregner automatisk næringsindhold (se afsnittet om datakilder nedenfor).
3. Under **Log Træning**: vælg type og varighed - forbrændte kalorier
   beregnes automatisk ud fra din vægt.
4. Under **Dashboard**: se dagens overblik, ugentlige gennemsnit, en
   ugentlig og en månedlig graf over kalorier ind/ud, makrofordeling, og
   hent en AI-anbefaling baseret på de seneste 7 dage.

## API-eksempler (curl/httpie)

Opret en bruger (vægt bruges til at beregne forbrændte kalorier):

```bash
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"name": "julius", "weight_kg": 82}'
```

Log et måltid (makroer beregnes automatisk):

```bash
curl -X POST http://localhost:8000/meals/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "food_name": "kylling", "grams": 200}'
```

Log et træningspas (forbrændte kalorier beregnes automatisk ud fra
brugerens vægt - skal ikke angives):

```bash
http POST localhost:8000/workouts/ \
  user_id:=1 workout_type="Løb" duration_minutes:=30
```

Hent dashboard-data (seneste 30 dages kalorier ind/ud):

```bash
curl http://localhost:8000/dashboard/1/daily-summary?days=30
```

Hent en AI-anbefaling:

```bash
curl http://localhost:8000/dashboard/1/recommendation
```

Se alle endpoints interaktivt på http://localhost:8000/docs.

## Tests og kodekvalitet

Kør fra `backend/`-mappen (kræver et lokalt virtuelt miljø med
`requirements.txt` installeret, eller kør inde i containeren):

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

pytest app/tests -v          # Unittests (26 tests)
mypy app --exclude app/tests # Statisk typetjek
flake8 app                   # Style-tjek
ruff check app                # Hurtig linting
```

Alle beregningsfunktioner (makroberegning, dags-/ugeaggregering,
LLM-anbefaling) er testet isoleret med mockede HTTP-kald, så testene
kører hurtigt og uden afhængighed af internettet eller en kørende Ollama.

## Projektstruktur

```
fitlog/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI-app og alle endpoints
│   │   ├── models.py           # SQLAlchemy-tabeller (User, Meal, Workout)
│   │   ├── schemas.py          # Pydantic request/response-modeller
│   │   ├── crud.py             # Databaseoperationer
│   │   ├── database.py         # Engine/session-opsætning + lette migrationer
│   │   ├── services/
│   │   │   ├── openfoodfacts.py # Lokal fødevaredatabase + Open Food Facts
│   │   │   ├── calories.py      # MET-baseret beregning af forbrændte kalorier
│   │   │   ├── llm.py           # Ollama/Mistral-integration
│   │   │   └── aggregation.py   # Pandas/NumPy-aggregering
│   │   └── tests/               # pytest-tests (38 stk.)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py                  # Indgangspunkt: st.navigation + tema
│   ├── api_client.py           # Samlet HTTP-klient mod backend
│   ├── styling.py               # Delt CSS til et mere moderne look
│   ├── .streamlit/config.toml   # Mørkt tema (farver, skrifttype)
│   ├── views/
│   │   ├── forside.py           # Brugervalg (navn + vægt)
│   │   ├── log_maaltid.py
│   │   ├── log_traening.py
│   │   └── dashboard.py
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── .env.example
└── README.md
```