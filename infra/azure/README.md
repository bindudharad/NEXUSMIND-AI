# NEXUSMIND AI Azure Deployment Blueprint

This folder documents the Azure-ready production shape for the enterprise AI operating system.

Recommended Azure services:

- Azure Container Apps for `nexusmind-api`, `nexusmind-web`, and realtime workers.
- Azure Monitor and Log Analytics for centralized application logs and metrics.
- Azure Blob Storage for document ingestion, generated reports, and model artifacts.
- Azure Database for PostgreSQL Flexible Server for relational workforce analytics.
- Azure Cosmos DB for MongoDB-compatible event and AI decision logs.
- Azure Cache for Redis for realtime cache, rate limits, and notification fanout.
- Azure Container Registry for signed frontend and backend images.
- Azure Kubernetes Service when deploying the Kubernetes manifests in `../k8s`.
- Azure Application Gateway or Nginx Ingress for TLS termination and WebSocket routing.
- Azure Key Vault for JWT secrets, database passwords, and LLM provider keys.

Operational expectations:

- Build images from `backend/Dockerfile` and `frontend/Dockerfile`.
- Apply `infra/k8s/infra-config.yaml` and `infra/k8s/ingress.yaml` for AKS.
- Map secrets through Key Vault references rather than checked-in environment files.
- Route `/api` and `/ws` to FastAPI, and all other paths to Next.js.
