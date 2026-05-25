# VoltEdge – Charging Session API

Denne version kører med Neon som produktionsdatabase og starter hele applikationen med én enkel kommando.

## Kom i gang

1. Klon repository
```bash
git clone https://github.com/<dit-brugernavn>/voltedge-session.git
cd voltedge-session
```

2. Kopiér `.env.example` til `.env` og indsæt din Neon connection string
```bash
cp .env.example .env
```

3. Installer dependencies til test- og helper-scripts
```bash
python -m pip install -r requirements.txt
```

4. Start hele stacken
```bash
docker compose up --build
```

Når stakken kører, er disse tilgængelige:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

## .env
Din `.env` skal indeholde mindst disse to variabler:
```env
DATABASE_URL=postgresql://[user]:[password]@[host].neon.tech/[dbname]?sslmode=require
API_KEY=skift-dette
```

## Verificering
Kør følgende for at sikre API og dokumentation:

PowerShell:
```powershell
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/docs
```

bash/WSL:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## Manuel test og helper-scripts
Der er helper-scripts i `tests/manual/`:
- `tests/manual/run_db_test.py` – test af Neon databaseforbindelse
- `tests/manual/run_load_test.py` – opret mange sessions mod API'et
- `tests/manual/inspect_schema.py` – inspektion af tabelstruktur i Neon

Eksempel:
```bash
python tests/manual/run_load_test.py --count 20 --start --end
```

## Serviceoversigt
- `api` – FastAPI backend
- `frontend` – Nginx, der serves `frontend/index.html`

## Noter
- Der er ingen lokal PostgreSQL-container i `docker-compose.yml`
- `api` læser `DATABASE_URL` og `API_KEY` direkte fra `.env`
- Hvis du ændrer `API_KEY`, skal `frontend/index.html` også bruge samme værdi

## Projektstruktur

| Folder | Formål |
|--------|--------|
| `app/` | Hele applikationen (FastAPI, domæne, data-adgang, metrikker) |
| `app/api/` | REST-endpoints til charging sessions |
| `app/db/` | Databaseopsætning (SQLAlchemy) og data-adgang (repositories) |
| `app/domain/` | Domænelogik – ChargingSession, value objects, business services |
| `tests/` | Unit- og integrationstests |
| `tests/manual/` | Manuelle helper-scripts |
| `frontend/` | HTML-dashboard til Nginx (vises på port 3000) |
| `monitoring/` | Legacy Prometheus/Grafana konfiguration (ikke aktiv i nuværende `docker-compose.yml`) |
| `.github/workflows/` | CI/CD pipeline for testing og building |

---

## Tech Stack

| Teknologi | Rolle |
|-----------|-------|
| Python 3.12 + FastAPI | API framework med automatisk OpenAPI-dokumentation |
| PostgreSQL (Neon) | Managed database for persistent sessiondata |
| SQLAlchemy | ORM og databaseadgang |
| Docker + Docker Compose | Containerisering og lokal orkestrering |
| GitHub Actions | CI/CD – test, byg og smoke test ved hvert push |
| pytest + httpx | Unit- og integrationstests |

---

## CI/CD

GitHub Actions-pipelinen kører automatisk ved hvert push til `main` eller `develop`:

1. Installer Python dependencies
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
