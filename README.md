# VoltEdge – Charging Session API

> **6. Semester eksamen · Økonomi og IT · Erhvervsakademi København**  
> Gruppe 3 – Aksel, Frederik og Mathias

---

## Hvad er dette projekt?

VoltEdge Mobility A/S er en dansk aktør inden for smart EV-ladeinfrastruktur med drift i Norden og Benelux. Virksomhedens platform er vokset organisk og har medført teknisk gæld i form af uklare datamodeller, fragmenterede processer og svag sporbarhed fra telemetri til faktura.

Dette repository er et eksamensprojekt der implementerer en MVP for **Charging Session**-domænet – det forretningsmæssigt mest kritiske domæne i VoltEdges værdikæde.

---

## Strategisk baggrund

VoltEdges tre centrale udfordringer er alle forankret i ét punkt i værdikæden: ladesessionen.

| Udfordring | Konsekvens |
|---|---|
| Fragmenteret datamodel og svag sporbarhed | Fejl i afregning, lav transparens |
| Kompleks og manuel afregningslogik | Operationel risiko, skaleringsbarrierer |
| Mangelfuld logning og monitorering | Langsom fejlfinding, ustabil drift |

Uden en veldefineret og sporbar sessionsmodel kan VoltEdge hverken automatisere afregning, skalere driften eller levere datadrevne services til partnere. Løsningen afgrænses derfor til **Charging Session** som core domain.

---

## Domain Driven Design

Projektet anvender Domain Driven Design (DDD) som arkitekturstrategi, fordi VoltEdges udfordringer i sin kerne er et sprogs- og definitionsproblem: hvornår starter en session, hvad er afregningsgrundlaget, og hvad udgør en gyldig pris?

### Bounded Context: Charging Session Management

MVP'en implementerer én bounded context. Billing & Settlement og Device Management er identificeret som selvstændige subdomæner uden for dette scope.

### Ubiquitous Language

Følgende begreber er anvendt konsekvent i kode, database og dokumentation:

| Begreb | Definition |
|---|---|
| `ChargingSession` | En komplet lade-hændelse for én bruger på én connector, fra oprettelse til afslutning |
| `SessionStatus` | INITIATED → ACTIVE → COMPLETED eller FAULTED |
| `EnergyDelivered` | Målt energi i kWh (value object – immutabel, validerer mod negative værdier) |
| `SessionCost` | Beregnet pris i DKK baseret på energiforbrug og tarif (value object – immutabel) |
| `TariffRate` | Pris pr. kWh i DKK |
| `StartSession` | Handling der igangsætter en aktiv ladesession |
| `EndSession` | Handling der afslutter sessionen og udløser automatisk prisberegning |

### DDD-byggeklodser i koden

| DDD-element | Klasse | Ansvar |
|---|---|---|
| Aggregate Root | `ChargingSession` | Håndhæver statusovergange – kan ikke sættes i ugyldig tilstand |
| Value Object | `EnergyDelivered` | Immutabel, afviser negative kWh-værdier |
| Value Object | `SessionCost` | Immutabel, beregnet pris med tilhørende tarif |
| Domain Service | `PricingService` | Beregner pris uden sideeffekter – fuldt testbar uden database |
| Domain Event | `SessionStarted` | Signalerer overgang INITIATED → ACTIVE |
| Domain Event | `SessionCompleted` | Signalerer afsluttet session med beregnet pris |

---

## Arkitektur

Applikationen følger en lagdelt arkitektur hvor DDD-modellen er uafhængig af framework og database:

```
┌─────────────────────────────────────┐
│  API-lag          app/api/routes.py │  HTTP, Pydantic-validering, ingen forretningslogik
├─────────────────────────────────────┤
│  Domain-lag       app/domain/       │  ChargingSession, value objects, PricingService
├─────────────────────────────────────┤
│  Persistenslag    app/db/           │  SQLAlchemy, SessionRepository, Neon-forbindelse
├─────────────────────────────────────┤
│  Infrastruktur    app/main.py, .env │  Konfiguration, logging, CORS, metrics
└─────────────────────────────────────┘
```

---

## Tech Stack

| Teknologi | Rolle | Begrundelse |
|---|---|---|
| Python 3.12 + FastAPI | API framework | Async, Pydantic-validering, automatisk OpenAPI-spec |
| PostgreSQL via Neon | Cloud-database | Managed, gratis, SSL, ACID-compliance |
| SQLAlchemy | ORM | Adskiller persistens fra domænelogik |
| Docker + Docker Compose | Containerisering | Reproducerbart miljø, to services: api + frontend |
| Nginx | Frontend server | Serves dashboard på port 3000 |
| GitHub Actions | CI/CD | Build, test og smoke test ved hvert push |
| pytest + httpx | Test | 14 unit tests + 11 integrationstests |

---

## Kom i gang

### Krav
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installeret og kørende
- En gratis [Neon](https://neon.tech)-konto med en PostgreSQL-database

### 1. Klon repository
```bash
git clone https://github.com/<dit-brugernavn>/voltedge-session.git
cd voltedge-session
```

### 2. Opsæt miljøvariabler
```bash
cp .env.example .env
```

Åbn `.env` og indsæt din Neon connection string:
```env
DATABASE_URL=postgresql://[user]:[password]@[host].neon.tech/[dbname]?sslmode=require
API_KEY=skift-dette-til-en-sikker-nøgle
```

### 3. Start applikationen
```bash
docker compose up --build
```

Når stacken kører:

| Service | URL |
|---|---|
| Frontend dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger dokumentation | http://localhost:8000/docs |

---

## API-endpoints

Alle POST-endpoints kræver headeren `X-API-Key: <din nøgle>`.

| Method | Endpoint | Beskrivelse |
|---|---|---|
| GET | `/health` | Sundhedstjek |
| GET | `/metrics` | Prometheus-metrikker |
| POST | `/sessions/` | Opret ny session (INITIATED) |
| POST | `/sessions/{id}/start` | Start session (→ ACTIVE) |
| POST | `/sessions/{id}/end` | Afslut med kWh og tarif (→ COMPLETED, pris beregnes) |
| GET | `/sessions/{id}` | Hent sessiondetaljer |
| GET | `/sessions/` | List alle sessioner |
| GET | `/sessions/stats/summary` | Aggregeret statistik til dashboard |

### Eksempel – komplet session livscyklus

```bash
# 1. Opret
curl -X POST http://localhost:8000/sessions/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d '{"charger_id": "CHG-01", "connector_id": "CON-1", "user_id": "USR-42"}'

# 2. Start (indsæt session_id fra svaret)
curl -X POST http://localhost:8000/sessions/<session_id>/start \
  -H "X-API-Key: dev-secret-key"

# 3. Afslut (15 kWh á 2,50 DKK = 37,50 DKK)
curl -X POST http://localhost:8000/sessions/<session_id>/end \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d '{"energy_kwh": 15.0, "tariff_rate": 2.50}'
```

---

## Tests

```bash
# Unit tests – kræver ikke database
python -m pytest tests/test_domain.py -v

# Integrationstests – kræver kørende PostgreSQL eller Neon
$env:DATABASE_URL="postgresql://volt:secret@localhost:5432/sessions"
$env:API_KEY="test-key"
python -m pytest tests/test_api.py -v

# Alle 25 tests
python -m pytest tests/ -v
```

### Manuel test og helper-scripts

```bash
# Test Neon-forbindelsen
python tests/manual/run_db_test.py

# Opret 20 sessioner mod API'et (load-test)
python tests/manual/run_load_test.py --count 20 --start --end

# Inspicér databaseskemaet i Neon
python tests/manual/inspect_schema.py
```

---

## CI/CD

GitHub Actions kører automatisk ved push til `main` og `develop`:

1. Installer dependencies
2. Kør unit tests (domænelogik uden database)
3. Start PostgreSQL-service og kør integrationstests
4. Byg Docker-image
5. Smoke test – start container, verificer `/health` svarer

Se `.github/workflows/ci.yml` for fuld konfiguration.

---

## Projektstruktur

```
voltedge-session/
├── app/
│   ├── domain/
│   │   ├── models.py        # ChargingSession, EnergyDelivered, SessionCost, SessionStatus
│   │   └── services.py      # PricingService
│   ├── api/
│   │   └── routes.py        # FastAPI endpoints
│   ├── db/
│   │   ├── database.py      # SQLAlchemy engine (Neon), ORM-model
│   │   └── repositories.py  # SessionRepository
│   ├── metrics.py           # Prometheus-metrikker
│   └── main.py              # App entry point, CORS, lifespan
├── tests/
│   ├── test_domain.py       # 14 unit tests
│   ├── test_api.py          # 11 integrationstests
│   └── manual/              # Helper-scripts til manuel test
├── frontend/
│   └── index.html           # Dashboard served af Nginx (port 3000)
├── monitoring/              # Legacy Prometheus/Grafana (ikke aktiv)
├── .github/workflows/
│   └── ci.yml               # GitHub Actions pipeline
├── docker-compose.yml       # api + frontend (Neon erstatter lokal db)
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

