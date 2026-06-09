# Module 2 - Cinematic Enterprise Command Center

## Architecture

Module 2 expands the command center into an executive operating surface. The backend exposes a dedicated intelligence API while the frontend composes multiple reusable panels around one demo-first workflow.

## Folder Structure

```text
backend/app/
  ai/
    burnout_model.py
    digital_twin.py
  api/v1/routes/
    intelligence.py
  schemas/
    intelligence.py
  services/
    intelligence_service.py

frontend/src/
  components/dashboard/
    ExecutiveAssistantPanel.tsx
    BurnoutHeatmap.tsx
    CybersecurityPanel.tsx
    SimulationConsole.tsx
  lib/
    intelligence-data.ts
  types/
    intelligence.ts
```

## Backend Code

The backend now includes:

- `GET /api/v1/intelligence/overview`
- Burnout scoring baseline in `backend/app/ai/burnout_model.py`
- Digital twin simulation baseline in `backend/app/ai/digital_twin.py`
- Structured response contracts in `backend/app/schemas/intelligence.py`

## Frontend Code

The command center now includes:

- Live CEO assistant panel
- Burnout and attrition heatmap
- AI cybersecurity response console
- Company time-machine simulation console
- Existing digital twin, forecasts, agents, metrics, and department matrix

## AI/ML Code

This module uses explainable baseline AI instead of opaque placeholder numbers:

- Burnout score combines overtime, meetings, sentiment, task completion, and absence.
- Digital twin simulation estimates delay probability, burnout delta, and revenue impact from scenario inputs.

These baselines are designed to be replaced by trained Scikit-learn, XGBoost, PyTorch, or TensorFlow models after real enterprise data pipelines are added.

## APIs

Authenticated endpoint:

```text
GET /api/v1/intelligence/overview
```

The endpoint returns burnout signals, security events, simulations, and executive assistant directives.

## Setup

Run the backend and frontend as described in the root README. The command center uses local demo data for static build reliability and mirrors the backend response shape so API wiring can be swapped in without changing component contracts.

## Deployment

The command center is compatible with the current Docker Compose, Nginx, Kubernetes, GitHub Actions, AWS, and Azure deployment assets. Heavy inference paths are isolated behind backend services so they can be moved to workers or model-serving processes when production traffic requires it.

## Scalability

- AI logic is isolated under `backend/app/ai`.
- API contracts are explicit through Pydantic and TypeScript types.
- Frontend panels are reusable and independently testable.
- Simulation and scoring functions can later be moved to asynchronous workers.

## Production Follow-Ups

- Add managed observability, model drift monitoring, and cost controls.
- Attach real people-systems, recruiting, CRM, identity, and document-ingestion connectors.
- Calibrate models against real customer datasets with privacy and governance controls.
