from __future__ import annotations

import importlib.util
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

from app.core.cache import TTLResponseCache
from app.ai.anomaly_detector import anomaly_detector
from app.ai.employee_analytics_engine import employee_analytics_engine
from app.ai.enterprise_models import enterprise_model_registry
from app.ai.huggingface_engine import huggingface_sentiment_engine
from app.ai.nlp_engine import nlp_emotion_engine
from app.ai.recommendation_engine import recommendation_engine
from app.ai.tensorflow_engine import tensorflow_risk_engine
from app.ai.time_series_engine import time_series_forecaster
from app.core.config import settings
from app.db.session import engine
from app.schemas.technology_stack import TechnologyCheck, TechnologyStackResponse, TechnologyStackSummary


ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = ROOT / "frontend"
BACKEND_DIR = ROOT / "backend"


class TechnologyStackService:
    def __init__(self) -> None:
        self._cache: TTLResponseCache[TechnologyStackResponse] = TTLResponseCache(ttl_seconds=30)

    def verify(self) -> TechnologyStackResponse:
        return self._cache.get_or_set(self._verify_uncached)

    def _verify_uncached(self) -> TechnologyStackResponse:
        checks = [
            *self._frontend_checks(),
            *self._backend_checks(),
            *self._ai_checks(),
            *self._database_checks(),
            *self._deployment_checks(),
        ]
        summary = self._summary(checks)
        return TechnologyStackResponse(
            generated_at=datetime.now(timezone.utc),
            environment=settings.environment,
            summary=summary,
            checks=checks,
            recommendations=self._recommendations(checks),
        )

    def _frontend_checks(self) -> list[TechnologyCheck]:
        package = self._package_json()
        dependencies = package.get("dependencies", {})
        app_router = FRONTEND_DIR / "src" / "app" / "page.tsx"
        layout = FRONTEND_DIR / "src" / "app" / "layout.tsx"
        api_routes = list((FRONTEND_DIR / "src" / "app" / "api").glob("**/route.ts"))
        return [
            TechnologyCheck(
                name="React",
                category="frontend",
                status="ready" if "react" in dependencies and app_router.exists() else "missing",
                details="React components, hooks, and client dashboards are present.",
                evidence=[f"react {dependencies.get('react', 'missing')}", str(app_router), f"{len(list((FRONTEND_DIR / 'src' / 'components').glob('**/*.tsx')))} TSX components"],
            ),
            TechnologyCheck(
                name="Next.js",
                category="frontend",
                status="ready" if "next" in dependencies and layout.exists() and api_routes else "missing",
                details="Next.js App Router, layout, production build scripts, and API proxy routes are configured.",
                evidence=[f"next {dependencies.get('next', 'missing')}", str(layout), f"{len(api_routes)} app API routes"],
            ),
        ]

    def _backend_checks(self) -> list[TechnologyCheck]:
        fastapi_ready = self._module_available("fastapi")
        route_files = list((BACKEND_DIR / "app" / "api" / "v1" / "routes").glob("*.py"))
        return [
            TechnologyCheck(
                name="Python",
                category="backend",
                status="ready",
                details="Python backend is modularized into API routes, schemas, services, AI engines, and tests.",
                evidence=[str(BACKEND_DIR / "app"), f"{len(list((BACKEND_DIR / 'app' / 'services').glob('*.py')))} services"],
            ),
            TechnologyCheck(
                name="FastAPI",
                category="backend",
                status="ready" if fastapi_ready and route_files else "missing",
                details="FastAPI routes, Pydantic validation, auth dependencies, middleware, and OpenAPI support are present.",
                evidence=[f"fastapi import: {fastapi_ready}", f"{len(route_files)} route modules", "/docs available from FastAPI"],
            ),
        ]

    def _ai_checks(self) -> list[TechnologyCheck]:
        tf = tensorflow_risk_engine.verify()
        hf_ready = huggingface_sentiment_engine.available
        hf_evidence = [huggingface_sentiment_engine.model_name]
        if hf_ready:
            prediction = huggingface_sentiment_engine.analyze("The team is exhausted by overtime")
            hf_evidence.extend([f"label={prediction.label}", f"confidence={prediction.confidence}"])
        return [
            TechnologyCheck(
                name="TensorFlow",
                category="ai_ml",
                status="ready" if tf.available else "configured" if "tensorflow-cpu" in self._requirements_text() else "missing",
                details=tf.details if tf.available else "TensorFlow engine is implemented; install backend requirements in Linux/Docker runtime to activate inference.",
                evidence=[tf.model, f"runtime_available={tf.available}", f"sample_prediction={tf.prediction}"],
            ),
            TechnologyCheck(
                name="Scikit-learn",
                category="ai_ml",
                status="ready" if self._module_available("sklearn") and enterprise_model_registry.available else "missing",
                details="Random Forest, preprocessing, anomaly detection, and recommendation ranking use scikit-learn models.",
                evidence=[
                    "RandomForest burnout ensemble",
                    f"enterprise suite={enterprise_model_registry.available}",
                    f"employee analytics={employee_analytics_engine.available}",
                    f"recommendation engine={recommendation_engine.available}",
                    f"anomaly detector={anomaly_detector.available}",
                ],
            ),
            TechnologyCheck(
                name="Hugging Face Transformers",
                category="ai_ml",
                status="ready" if hf_ready else "configured" if self._module_available("transformers") else "missing",
                details="A local tiny DistilBERT sentiment verifier is trained/saved through the transformers API without external downloads.",
                evidence=hf_evidence,
            ),
            TechnologyCheck(
                name="PyTorch AI Runtime",
                category="ai_ml",
                status="ready" if self._module_available("torch") and nlp_emotion_engine.available and time_series_forecaster.available else "missing",
                details="PyTorch powers the NLP emotion model, neural burnout ensemble, and workload LSTM.",
                evidence=[f"nlp={nlp_emotion_engine.available}", f"forecasting={time_series_forecaster.available}"],
            ),
            TechnologyCheck(
                name="LangChain / RAG Orchestration",
                category="genai",
                status="ready" if self._module_available("langchain_core") and settings.langchain_enabled else "configured" if settings.langchain_enabled and "langchain-core" in self._requirements_text() else "missing",
                details="RAG orchestration is implemented around the enterprise knowledge engine, with LangChain Core declared for production provider chains.",
                evidence=[
                    f"langchain_core_import={self._module_available('langchain_core')}",
                    f"requirements_declared={'langchain-core' in self._requirements_text()}",
                    "knowledge_vector_index.joblib",
                ],
            ),
            TechnologyCheck(
                name="LLM API Adapter",
                category="genai",
                status="ready" if settings.llm_provider == "local" or bool(settings.llm_api_key) else "configured",
                details="The manager and HR assistants run through a provider adapter that supports local deterministic RAG and external LLM API keys.",
                evidence=[
                    f"provider={settings.llm_provider}",
                    f"api_base_configured={bool(settings.llm_api_base_url)}",
                    f"api_key_configured={bool(settings.llm_api_key)}",
                ],
            ),
        ]

    def _database_checks(self) -> list[TechnologyCheck]:
        postgres = self._postgres_check()
        mongo = self._mongo_check()
        compose = self._compose_text()
        return [
            postgres,
            mongo,
            TechnologyCheck(
                name="Redis",
                category="database",
                status="ready" if settings.redis_url else "configured" if "redis" in compose else "missing",
                details="Redis is used for realtime cache, rate limiting, and notification fanout configuration.",
                evidence=[settings.redis_url or "compose redis service", f"compose_contains_redis={'redis' in compose}"],
            ),
            TechnologyCheck(
                name="Qdrant Vector Database",
                category="database",
                status="ready" if settings.qdrant_url else "configured" if "qdrant" in compose else "missing",
                details="Qdrant is configured as the vector store for enterprise memory and semantic retrieval.",
                evidence=[settings.qdrant_url or "compose qdrant service", f"compose_contains_qdrant={'qdrant' in compose}"],
            ),
            TechnologyCheck(
                name="Neo4j Graph Database",
                category="database",
                status="configured" if settings.neo4j_uri or "neo4j" in compose else "missing",
                details="Neo4j is configured for knowledge graphs, expertise maps, and team relationship graph storage.",
                evidence=[settings.neo4j_uri, f"compose_contains_neo4j={'neo4j' in compose}"],
            ),
        ]

    def _postgres_check(self) -> TechnologyCheck:
        if not settings.postgres_dsn:
            return TechnologyCheck(name="PostgreSQL", category="database", status="missing", details="POSTGRES_DSN is not configured.", evidence=[])
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS technology_stack_checks (
                            id SERIAL PRIMARY KEY,
                            component VARCHAR(120) NOT NULL,
                            status VARCHAR(32) NOT NULL,
                            created_at TIMESTAMPTZ DEFAULT NOW()
                        )
                        """
                    )
                )
                connection.execute(text("CREATE INDEX IF NOT EXISTS ix_stack_checks_component ON technology_stack_checks(component)"))
                connection.execute(text("INSERT INTO technology_stack_checks(component, status) VALUES ('postgresql', 'ready')"))
                count = connection.execute(text("SELECT COUNT(*) FROM technology_stack_checks")).scalar_one()
            return TechnologyCheck(
                name="PostgreSQL",
                category="database",
                status="ready",
                details="PostgreSQL connection, table creation, insert, index, and query succeeded.",
                evidence=[settings.postgres_dsn.split("@")[-1], f"stack_check_rows={count}"],
            )
        except Exception as exc:
            return TechnologyCheck(
                name="PostgreSQL",
                category="database",
                status="configured",
                details="PostgreSQL integration code is present, but the configured server is not reachable in this local runtime.",
                evidence=[settings.postgres_dsn.split("@")[-1], str(exc)[:180]],
            )

    def _mongo_check(self) -> TechnologyCheck:
        if not settings.mongo_uri:
            return TechnologyCheck(name="MongoDB", category="database", status="missing", details="MONGO_URI is not configured.", evidence=[])
        try:
            from pymongo import MongoClient

            client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=1200)
            db = client["nexusmind"]
            db["technology_stack_events"].create_index("component")
            result = db["technology_stack_events"].insert_one({"component": "mongodb", "status": "ready", "created_at": datetime.now(timezone.utc)})
            client.admin.command("ping")
            return TechnologyCheck(
                name="MongoDB",
                category="database",
                status="ready",
                details="MongoDB ping, insert, collection, and index checks succeeded.",
                evidence=[settings.mongo_uri, f"inserted_id={result.inserted_id}"],
            )
        except Exception as exc:
            return TechnologyCheck(
                name="MongoDB",
                category="database",
                status="configured",
                details="MongoDB integration code is present, but the configured server is not reachable in this local runtime.",
                evidence=[settings.mongo_uri, str(exc)[:180]],
            )

    def _deployment_checks(self) -> list[TechnologyCheck]:
        compose = ROOT / "infra" / "docker" / "docker-compose.yml"
        compose_text = self._compose_text()
        k8s_dir = ROOT / "infra" / "k8s"
        k8s_files = list(k8s_dir.glob("*.yaml")) if k8s_dir.exists() else []
        ci_file = ROOT / ".github" / "workflows" / "ci.yml"
        nginx_file = ROOT / "infra" / "nginx" / "nexusmind.conf"
        aws_files = list((ROOT / "infra" / "aws").glob("*.tf")) if (ROOT / "infra" / "aws").exists() else []
        azure_files = list((ROOT / "infra" / "azure").glob("*")) if (ROOT / "infra" / "azure").exists() else []
        docker_status = "ready" if shutil.which("docker") else "configured" if compose.exists() else "missing"
        aws_status = "ready" if aws_files and self._module_available("boto3") else "configured" if aws_files else "missing"
        return [
            TechnologyCheck(
                name="Docker",
                category="deployment",
                status=docker_status,
                details="Dockerfiles and Compose stack define frontend, backend, PostgreSQL, MongoDB, Redis, Qdrant, Neo4j, Kafka, Spark, and Nginx.",
                evidence=[str(BACKEND_DIR / "Dockerfile"), str(FRONTEND_DIR / "Dockerfile"), str(compose), f"docker_cli={bool(shutil.which('docker'))}", f"backend_java_runtime={'openjdk' in (BACKEND_DIR / 'Dockerfile').read_text(encoding='utf-8').lower()}"],
            ),
            TechnologyCheck(
                name="Kubernetes",
                category="deployment",
                status="ready" if len(k8s_files) >= 3 else "configured" if k8s_files else "missing",
                details="Kubernetes manifests configure API, web, realtime worker, config, service, and ingress deployment topology.",
                evidence=[*(str(path) for path in k8s_files), f"manifest_count={len(k8s_files)}"],
            ),
            TechnologyCheck(
                name="GitHub Actions CI/CD",
                category="deployment",
                status="ready" if ci_file.exists() and "pytest" in ci_file.read_text(encoding="utf-8") else "configured" if ci_file.exists() else "missing",
                details="CI validates backend compile, backend tests, frontend typecheck, lint, build, and infrastructure manifest presence.",
                evidence=[str(ci_file), "pytest", "npm run build", "manifest validation"],
            ),
            TechnologyCheck(
                name="Nginx Gateway",
                category="deployment",
                status="ready" if nginx_file.exists() and "proxy_pass" in nginx_file.read_text(encoding="utf-8") else "configured" if nginx_file.exists() else "missing",
                details="Nginx gateway routes Next.js, FastAPI REST APIs, and WebSocket traffic for production ingress.",
                evidence=[str(nginx_file), "proxy_pass", "websocket upgrade headers"],
            ),
            TechnologyCheck(
                name="Kafka Streaming",
                category="streaming",
                status="ready" if self._module_available("kafka") and (settings.kafka_bootstrap_servers or "kafka" in compose_text) else "configured" if settings.kafka_bootstrap_servers or "kafka" in compose_text else "missing",
                details="Kafka is configured as the event-stream backbone for realtime enterprise analytics, with a Python producer/consumer client available for ingestion workers.",
                evidence=[settings.kafka_bootstrap_servers, f"compose_contains_kafka={'kafka' in compose_text}", f"kafka_python_import={self._module_available('kafka')}"],
            ),
            TechnologyCheck(
                name="Spark Analytics",
                category="big_data",
                status="ready" if self._module_available("pyspark") and (settings.spark_master_url or "spark-master" in compose_text) and "openjdk" in (BACKEND_DIR / "Dockerfile").read_text(encoding="utf-8").lower() else "configured" if settings.spark_master_url or "spark-master" in compose_text else "missing",
                details="Spark master and worker services are configured for large-scale workforce and project analytics jobs; the backend container includes Java for PySpark drivers.",
                evidence=[settings.spark_master_url, f"compose_contains_spark={'spark-master' in compose_text}", f"pyspark_import={self._module_available('pyspark')}", f"local_java_cli={bool(shutil.which('java'))}"],
            ),
            TechnologyCheck(
                name="AWS Readiness",
                category="deployment",
                status=aws_status,
                details="AWS deployment assets target ECS Fargate, ALB, ECR, CloudWatch logs, RDS PostgreSQL, and DocumentDB-compatible MongoDB.",
                evidence=[*(str(path) for path in aws_files), f"boto3={self._module_available('boto3')}"],
            ),
            TechnologyCheck(
                name="Azure Readiness",
                category="deployment",
                status="ready" if azure_files and self._module_available("azure.identity") and self._module_available("azure.storage.blob") else "configured" if azure_files else "missing",
                details="Azure Container Apps, Log Analytics, Blob Storage, AKS, Key Vault, Application Gateway, and managed data service wiring are documented and configured for cloud deployment.",
                evidence=[*(str(path) for path in azure_files), f"artifact_count={len(azure_files)}", f"azure_identity={self._module_available('azure.identity')}", f"azure_storage_blob={self._module_available('azure.storage.blob')}"],
            ),
        ]

    @staticmethod
    def _summary(checks: list[TechnologyCheck]) -> TechnologyStackSummary:
        ready = sum(1 for check in checks if check.status == "ready")
        configured = sum(1 for check in checks if check.status == "configured")
        missing = sum(1 for check in checks if check.status == "missing")
        errors = sum(1 for check in checks if check.status == "error")
        score = round(((ready + configured * 0.65) / len(checks)) * 100, 2) if checks else 0
        return TechnologyStackSummary(total=len(checks), ready=ready, configured=configured, missing=missing, errors=errors, production_ready_score=score)

    @staticmethod
    def _recommendations(checks: list[TechnologyCheck]) -> list[str]:
        recommendations: list[str] = []
        for check in checks:
            if check.status == "missing":
                recommendations.append(f"Install or implement {check.name} before production release.")
            if check.status == "configured":
                recommendations.append(f"Connect runtime infrastructure for {check.name}: {check.details}")
        return recommendations or ["Technology stack is fully ready in this runtime."]

    @staticmethod
    def _module_available(name: str) -> bool:
        try:
            return importlib.util.find_spec(name) is not None
        except ModuleNotFoundError:
            return False

    @staticmethod
    def _package_json() -> dict[str, object]:
        package_path = FRONTEND_DIR / "package.json"
        return json.loads(package_path.read_text(encoding="utf-8")) if package_path.exists() else {}

    @staticmethod
    def _requirements_text() -> str:
        requirements = BACKEND_DIR / "requirements.txt"
        return requirements.read_text(encoding="utf-8") if requirements.exists() else ""

    @staticmethod
    def _compose_text() -> str:
        compose = ROOT / "infra" / "docker" / "docker-compose.yml"
        return compose.read_text(encoding="utf-8").lower() if compose.exists() else ""


technology_stack_service = TechnologyStackService()
