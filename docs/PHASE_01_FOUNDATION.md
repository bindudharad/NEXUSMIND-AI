# Foundation Architecture

## Architecture

NEXUSMIND AI is organized as a monorepo with clear product and system boundaries.

```text
NEXUSMIND AI/
  backend/       FastAPI services, auth, data models, AI service boundaries
  frontend/      Next.js control room UI
  packages/      Shared contracts and typed schemas
  infra/         Docker and deployment manifests
  docs/          Architecture notes and phase documentation
  scripts/       Developer automation
```

## Backend

The backend is a modular FastAPI service:

- `app/api/v1`: versioned HTTP routes.
- `app/core`: settings, security, and app configuration.
- `app/models`: domain models and RBAC enums.
- `app/schemas`: API request and response contracts.
- `app/services`: business logic and data access boundaries.
- `app/ai`: ML, NLP, forecasting, RAG, graph intelligence, and model orchestration modules.
- `app/db`: database session and repository setup.

Core service examples:

- `GET /health`: platform health.
- `POST /api/v1/auth/login`: demo JWT login.
- `GET /api/v1/auth/me`: authenticated user profile.
- `GET /api/v1/dashboard/overview`: enterprise command snapshot.
- `GET /api/v1/platform/operating-system`: complete platform capability audit.
- `GET /api/v1/system/technology-stack`: technology and infrastructure readiness.
- `GET /api/v1/system/enterprise-ai-features`: enterprise AI coverage audit.

## Frontend

The frontend is a Next.js App Router application using:

- React and TypeScript for typed UI.
- Tailwind CSS for a custom dark enterprise design system.
- Framer Motion for cinematic but restrained transitions.
- Recharts for predictive intelligence views.
- Three.js through `@react-three/fiber` for the first control-room visual.

The first screen is the working executive command center, not a marketing landing page.

## Authentication And RBAC

Roles are represented consistently across backend and shared contracts:

- CEO
- HR
- Manager
- Employee
- Admin

JWT access tokens are implemented with a demo identity provider for local validation. Production deployments should replace it with SSO/OAuth, refresh tokens, persistent user storage, password policy controls, and audit logs without changing the route shape.

## Database Setup

Docker Compose provisions:

- PostgreSQL for relational enterprise data.
- MongoDB for flexible events and simulation states.
- Redis for caching, queues, and real-time state.
- Qdrant for vector search and RAG memory.
- Neo4j for graph relationships.
- Kafka for event streaming.
- Spark for analytics processing.
- API, web, and Nginx gateway services.

## Deployment

The repository includes Docker Compose, backend/frontend Dockerfiles, Kubernetes starter manifests, Nginx gateway config, GitHub Actions CI, AWS Terraform starter, and Azure Container Apps blueprint. Production promotion requires immutable container images, external managed data services, and real secret-manager injection.

## Scalability Notes

- API versioning is present from the start.
- AI modules are isolated behind service boundaries.
- Shared contracts prevent frontend/backend drift.
- Environment settings are centralized and typed.
- Worker, queue, streaming, and model-serving concerns are kept separate from route handlers through service boundaries and infrastructure configuration.
