# ProphetAI — Web-Based AI Real Estate Analytics Platform

> **Instant AI-powered property valuations and "Red Flag" detection — paste a listing URL, get insights in seconds.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org)
[![Django 4.2](https://img.shields.io/badge/Django-4.2-green.svg)](https://djangoproject.com)

---

## ✨ MVP Features

### 🏷️ Smart Pricing Engine
ProphetAI uses a **Kyrgyzstan real-estate price benchmark heuristic** and **Google Gemini** multimodal analysis to estimate a property's price. The backend can optionally use a trained model when a compatible model artifact is supplied; **no trained XGBoost artifact is included in this repository**. A supported listing URL can be processed to extract property details for analysis, subject to source-site availability and API access.

### 📊 Investment Score Dashboards
Every analysed property gets a composite **Investment Score (0–100)** displayed on a FinTech-style dashboard with:
- Estimated vs. listing price delta
- Rental yield projection
- Estimated annual appreciation based on city-level assumptions
- Comparable listings when the scraper can retrieve them

### 🖼️ AI-Vision Photo Analysis
The platform sends property listing photos to the **Gemini Vision API** and returns structured *Photo Insight* cards highlighting:
- Renovation requirements and estimated cost
- Condition rating per room
- "Red Flags" (water stains, structural cracks, outdated wiring panels, etc.)
- Curb-appeal score

---

## 🔎 Methodology & limitations

This is a hackathon MVP, not a certified valuation or structural inspection service.

- **Valuation:** without an external trained model artifact, `backend/services/pricing_service.py` uses city, size, building condition, housing series, property type, and land benchmarks. When Gemini returns an estimate, the service blends it with its heuristic estimate.
- **Interval:** the displayed `confidence_interval` is currently calculated as **estimated price ±12%** in code. It is a fixed range, **not a statistically calibrated prediction interval**.
- **Rental yield & appreciation:** these are rules-of-thumb and city-level assumptions, not guaranteed future returns.
- **Image-based red flags:** Gemini generates suggested observations from descriptions/photos. They require independent professional verification.
- **Comparable listings:** the result depends on successful retrieval; it can be empty. The repository includes XGBoost as a dependency, but no checked-in model artifact or publicly documented validation metrics.

See [pricing service](backend/services/pricing_service.py) and [Gemini service](backend/services/gemini_service.py) for implementation details.

---

## 🏗️ Architecture

```
ProphetAI/
├── backend/                  # Django + DRF REST API
│   ├── prophetai/            # Django project settings
│   ├── properties/           # Core app: models, views, serializers
│   ├── services/             # AI service modules
│   │   ├── gemini_service.py # Google Gemini multimodal integration
│   │   └── pricing_service.py# KG price heuristic and optional model loader
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # Next.js 15 (TypeScript + Tailwind CSS)
│   ├── src/
│   │   ├── app/              # App Router pages
│   │   │   ├── page.tsx      # Landing / URL submission
│   │   │   ├── dashboard/    # Properties dashboard
│   │   │   └── analysis/[id] # Detailed analysis view
│   │   ├── components/       # Reusable UI components
│   │   └── lib/              # API client, utilities
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml        # Compose: backend + frontend + PostgreSQL + Redis
```

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- A **Google Gemini API key** ([get one here](https://aistudio.google.com/app/apikey))

### 1. Clone & configure
```bash
git clone https://github.com/zeuscode-tech/ProphetAi.git
cd ProphetAi
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Start all services
```bash
docker compose up --build
```

| Service   | URL                         |
|-----------|-----------------------------|
| Frontend  | http://localhost:3000       |
| Backend API | http://localhost:8000/api |
| Django Admin | http://localhost:8000/admin |

### 3. Apply migrations & create superuser
```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

---

## 🔧 Local Development (without Docker)

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in values
python manage.py migrate
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL
npm run dev
```

---

## 🔑 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | *(required)* |
| `DATABASE_URL` | PostgreSQL connection string | *(required)* |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `GEMINI_API_KEY` | Google Gemini API key | *(required)* |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost` |
| `DEBUG` | Django debug mode | `False` |
| `NEXT_PUBLIC_API_URL` | Backend API base URL (frontend) | `http://localhost:8000/api` |

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15.3.9, React 19, TypeScript, Tailwind CSS |
| Backend API | Django >=4.2,<5.0, Django REST Framework |
| AI / ML | Google Gemini 2.5 Flash (multimodal), price benchmark heuristics; optional trained model support |
| Database | PostgreSQL 15 |
| Cache / Queue | Redis 7, Celery |
| Containerisation | Docker, Docker Compose |

---

## 📄 License

This repository currently has no `LICENSE` file. Do not assume an open-source license; contact the repository owners about reuse permissions.
