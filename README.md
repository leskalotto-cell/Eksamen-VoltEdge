# VoltEdge – Charging Session API

MVP til styring af EV-ladesessioner, udviklet som eksamensprojekt for **Økonomi og IT, 6.2 semestereksamen** på Erhvervsakademi København.

Applikationen implementerer **Charging Session**-domænet fra VoltEdge Mobility A/S-casen ved hjælp af Domain Driven Design, FastAPI og PostgreSQL.

---

## Kom i gang

### Krav
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installeret og kørende

### Start applikationen

```bash
# 1. Klon repository
git clone https://github.com/<dit-brugernavn>/voltedge-session.git
cd voltedge-session

# 2. Kopiér .env.example til .env og sæt din Neon DATABASE_URL
cp .env.example .env

# 3. Start API, database, Prometheus og Grafana med Docker Compose
docker compose up --build
```

API'et er nu tilgængeligt på **http://localhost:8000**

Frontend-dashboardet er tilgængeligt på **http://localhost:3000**

Prometheus er tilgængeligt på **http://localhost:9090**

Prometheus er tilgængeligt på **http://localhost:9090**

Grafana er tilgængeligt på **http://localhost:3001**

---

## API dokumentation

FastAPI genererer automatisk interaktiv dokumentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Endpoints

| Method | Endpoint | Beskrivelse |
|--------|----------|-------------|
| GET | `/health` | Sundhedstjek |
| GET | `/metrics` | Prometheus metrikker |
| POST | `/sessions/` | Opret ny session (INITIATED) |
| POST | `/sessions/{id}/start` | Start session (→ ACTIVE) |
| POST | `/sessions/{id}/end` | Afslut session med kWh og tarif (→ COMPLETED) |
| GET | `/sessions/{id}` | Hent sessiondetaljer |
| GET | `/sessions/` | List alle sessioner |
| GET | `/sessions/stats/summary` | Aggregeret statistik til BI |

### Overvågning og Grafana

Applikationen eksponerer Prometheus-metrikker på `/metrics`. Du kan starte hele stakken med Docker Compose og få:

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

Grafana er forudkonfigureret med en Prometheus-datasource og et dashboard til `voltedge_request_count` og `voltedge_session_events_total`.

### Autentificering

Alle POST-endpoints kræver en API-nøgle i headeren:

```
X-API-Key: dev-secret-key
```

(Standardnøglen i dev-miljøet. Sæt `API_KEY` i `.env` til produktion.)

---

## Eksempel – komplet session livscyklus

```bash
# 1. Opret session
curl -X POST http://localhost:8000/sessions/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d '{"charger_id": "CHG-01", "connector_id": "CON-1", "user_id": "USR-42"}'

# Gem session_id fra svaret, fx:
SESSION_ID="<indsæt-session-id-her>"

# 2. Start session
curl -X POST http://localhost:8000/sessions/$SESSION_ID/start \
  -H "X-API-Key: dev-secret-key"

# 3. Afslut session (15 kWh á 2,50 DKK = 37,50 DKK)
curl -X POST http://localhost:8000/sessions/$SESSION_ID/end \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d '{"energy_kwh": 15.0, "tariff_rate": 2.50}'

# 4. Se statistik
curl http://localhost:8000/sessions/stats/summary
```

---

## Kør tests lokalt

```bash
# Installer dependencies
pip install -r requirements.txt

# Kopiér .env.example til .env og indsæt din Neon DATABASE_URL
cp .env.example .env
```

```bash
# Kør unit tests (kræver ikke database)
pytest tests/test_domain.py -v

# Kør integrationstests (kræver kørende PostgreSQL eller Neon)
pytest tests/test_api.py -v
```

> Bemærk: appen læser `DATABASE_URL` fra `.env` via `python-dotenv`.

---

## Projektstruktur

```
voltedge-session/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point + middleware
│   ├── metrics.py                # Prometheus metrics (request count, latency, session events)
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py             # REST endpoints for charging sessions
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py           # SQLAlchemy setup, engine, ORM models
│   │   └── repositories.py       # SessionRepository (data access layer)
│   └── domain/
│       ├── __init__.py
│       ├── models.py             # ChargingSession (Aggregate Root), value objects
│       └── services.py           # PricingService (Domain Service)
├── tests/
│   ├── __init__.py
│   ├── test_domain.py            # Unit tests – domænelogik og invarianter
│   └── test_api.py               # Integrationstests – alle endpoints
├── frontend/
│   └── index.html                # Dashboard served by Nginx (docker-compose)
├── monitoring/
│   ├── prometheus.yml            # Prometheus scrape config
│   └── grafana/
│       ├── dashboards/           # Grafana JSON dashboards
│       └── provisioning/         # Grafana datasources & dashboard providers
├── .github/
│   └── workflows/
│       └── ci.yml                # GitHub Actions CI/CD pipeline
├── docker-compose.yml            # Full stack: API + DB + Prometheus + Grafana + Nginx
├── Dockerfile                    # Python API container image
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template (copy to .env)
├── .env                          # Local environment (git-ignored)
├── .gitignore
└── README.md
```

### Mappers formål

| Folder | Formål |
|--------|--------|
| `app/` | Hele applikationen (FastAPI, domæne, data-adgang, metrikker) |
| `app/api/` | REST-endpoints til charging sessions |
| `app/db/` | Databaseopsætning (SQLAlchemy) og data-adgang (repositories) |
| `app/domain/` | Domænelogik – ChargingSession, value objects, business services |
| `tests/` | Unit- og integrationstests |
| `frontend/` | HTML-dashboard til Nginx (vises på port 3000) |
| `monitoring/` | Prometheus-config + Grafana-dashboards |
| `.github/workflows/` | CI/CD pipeline for testing og building |

---

---

## Tech Stack

| Teknologi | Rolle |
|-----------|-------|
| Python 3.12 + FastAPI | API framework med automatisk OpenAPI-dokumentation |
| PostgreSQL 16 | Relationel database – ACID-compliant sessionsdata |
| SQLAlchemy | ORM og databaseadgang |
| Docker + Docker Compose | Containerisering og lokal orkestrering |
| GitHub Actions | CI/CD – test, byg og smoke test ved hvert push |
| pytest + httpx | Unit- og integrationstests |

---

## CI/CD

GitHub Actions-pipelinen kører automatisk ved hvert push til `main` eller `develop`:

1. Installer Python-dependencies
2. Kør unit tests mod domænelogikken
3. Kør integrationstests mod rigtig PostgreSQL
4. Byg Docker image
5. Smoke test – verificer at containeren starter og `/health` svarer

---

## DDD-begreber i koden

| DDD-element | Implementering |
|-------------|---------------|
| Aggregate Root | `ChargingSession` – håndhæver statusovergange |
| Value Object | `EnergyDelivered`, `SessionCost` – immutable, ingen identitet |
| Domain Service | `PricingService` – beregner pris uden sideeffekter |
| Ubiquitous Language | Begreber som `charger_id`, `energy_kwh`, `tariff_rate` er konsistente fra API til database |
| Bounded Context | Charging Session Management – afgrænset fra Billing og Device Management |
