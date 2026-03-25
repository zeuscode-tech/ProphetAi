# ProphetAI — Web-Based AI Real Estate Analytics Platform

> **Instant AI-powered property valuations and "Red Flag" detection — paste a listing URL, get insights in seconds.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![Django 4.2](https://img.shields.io/badge/Django-4.2-green.svg)](https://djangoproject.com)

---

## ✨ MVP Features

### 🏷️ Smart Pricing Engine
ProphetAI combines a **Scikit-learn XGBoost** regression model trained on comparable sales with **Google Gemini** multimodal analysis to produce a fair-market value estimate with confidence intervals. Users paste any publicly accessible listing URL; the backend scrapes structured data (beds, baths, sqft, lot size, location) and runs it through the model instantly.

### 📊 Investment Score Dashboards
Every analysed property gets a composite **Investment Score (0–100)** displayed on a FinTech-style dashboard with:
- Estimated vs. listing price delta
- Rental yield projection
- Neighbourhood appreciation trend (12-month)
- Comparable properties table

### 🖼️ AI-Vision Photo Analysis
The platform sends property listing photos to the **Gemini Vision API** and returns structured *Photo Insight* cards highlighting:
- Renovation requirements and estimated cost
- Condition rating per room
- "Red Flags" (water stains, structural cracks, outdated wiring panels, etc.)
- Curb-appeal score

---

## 🏗️ Architecture

```
ProphetAI/
├── backend/                  # Django + DRF REST API
│   ├── prophetai/            # Django project settings
│   ├── properties/           # Core app: models, views, serializers
│   ├── services/             # AI service modules
│   │   ├── gemini_service.py # Google Gemini multimodal integration
│   │   └── pricing_service.py# XGBoost price prediction engine
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # Next.js 14 (TypeScript + Tailwind CSS)
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
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend API | Django 4.2, Django REST Framework |
| AI / ML | Google Gemini 1.5 Pro (multimodal), XGBoost |
| Database | PostgreSQL 15 |
| Cache / Queue | Redis 7, Celery |
| Containerisation | Docker, Docker Compose |

---

## 📄 License

MIT © 2024 ZeusCode Tech
