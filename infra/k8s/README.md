# Kubernetes

The Kubernetes directory contains deployable starter manifests for the NEXUSMIND API, web app, config, secret references, service exposure, and ingress routing. The manifests are designed for promotion into a managed cluster after production images, external databases, and secret backends are provisioned.

Included workloads and resources:

- `nexusmind-api`
- `nexusmind-web`
- API and web services
- Shared config map
- Secret references for runtime credentials
- HTTP ingress for frontend and API traffic
- Readiness and liveness probes for API and web
- CPU/memory requests and limits for API, web, and stream worker
- HorizontalPodAutoscalers for API and web
- PodDisruptionBudgets for rolling deploy resilience
- NetworkPolicy for API ingress scoping

Production hardening checklist:

- Publish the immutable image tags referenced in the manifests before applying them to a cluster.
- Create `nexusmind-api-secrets` from a real secret manager.
- Attach managed PostgreSQL, MongoDB, Redis, Qdrant, Neo4j, Kafka, and Spark endpoints.
- Add observability sidecars or OpenTelemetry collectors for the target cluster.
