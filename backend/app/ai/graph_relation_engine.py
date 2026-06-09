from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

from app.schemas.team_compatibility import TeamCompatibilityPair, TeamEmployeeProfile


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
GRAPH_MODEL_PATH = ARTIFACT_DIR / "graphsage_team_relations.pt"
METRICS_PATH = ARTIFACT_DIR / "graphsage_team_relations_metrics.json"


@dataclass(frozen=True)
class GraphNodePrediction:
    employee_id: str
    embedding: list[float]
    compatibility_projection: float
    conflict_projection: float
    burnout_spread_risk: float
    leadership_influence: float


@dataclass(frozen=True)
class GraphInference:
    nodes: list[GraphNodePrediction]
    edge_attention: dict[frozenset[str], float]
    metrics: dict[str, float | int | str]


class GraphSAGERelationNet(torch.nn.Module):
    def __init__(self, input_dim: int = 10, hidden_dim: int = 16, output_dim: int = 4) -> None:
        super().__init__()
        self.self_projection = torch.nn.Linear(input_dim, hidden_dim)
        self.neighbor_projection = torch.nn.Linear(input_dim, hidden_dim)
        self.output = torch.nn.Sequential(
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, output_dim),
            torch.nn.Sigmoid(),
        )

    def embed(self, features: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        neighbor_features = adjacency @ features
        return torch.relu(self.self_projection(features) + self.neighbor_projection(neighbor_features))

    def forward(self, features: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        return self.output(self.embed(features, adjacency))


class GraphRelationEngine:
    model_name = "PyTorch GraphSAGE Team Relation Network"
    architecture = "GraphSAGE mean aggregation with learned neighbor projection and relationship attention scoring"
    feature_names = [
        "productivity",
        "stress",
        "sentiment",
        "task_completion",
        "meeting_participation",
        "collaboration_frequency",
        "leadership",
        "burnout",
        "workload",
        "focus_ratio",
    ]

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.model = GraphSAGERelationNet(input_dim=len(self.feature_names))
        self.metrics_data: dict[str, float | int | str] = {}
        self._load_or_train()

    @property
    def available(self) -> bool:
        return GRAPH_MODEL_PATH.exists() and METRICS_PATH.exists()

    def _load_or_train(self) -> None:
        if GRAPH_MODEL_PATH.exists() and METRICS_PATH.exists():
            self.model.load_state_dict(torch.load(GRAPH_MODEL_PATH, map_location="cpu", weights_only=True))
            self.model.eval()
            self.metrics_data = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
            return
        self.train()

    def train(self) -> dict[str, float | int | str]:
        rng = np.random.default_rng(7272)
        features = rng.beta(2.4, 2.2, size=(96, len(self.feature_names))).astype(np.float32)
        # Stress, burnout, and workload need wider high-risk examples.
        features[:, 1] = rng.beta(2.2, 2.0, size=96)
        features[:, 7] = rng.beta(2.0, 2.7, size=96)
        features[:, 8] = rng.beta(2.5, 2.1, size=96)
        adjacency = rng.random((96, 96)).astype(np.float32)
        adjacency = (adjacency + adjacency.T) / 2
        adjacency = np.where(adjacency > 0.82, adjacency, 0)
        np.fill_diagonal(adjacency, 1.0)
        adjacency = self._normalize_adjacency(adjacency)

        productivity = features[:, 0]
        stress = features[:, 1]
        sentiment = features[:, 2]
        task_completion = features[:, 3]
        meeting = features[:, 4]
        collaboration = features[:, 5]
        leadership = features[:, 6]
        burnout = features[:, 7]
        workload = features[:, 8]
        focus = features[:, 9]
        neighbor_pressure = adjacency @ ((stress + burnout + workload) / 3)
        compatibility = np.clip(0.24 * productivity + 0.2 * collaboration + 0.16 * sentiment + 0.14 * task_completion + 0.1 * focus + 0.08 * leadership - 0.08 * stress, 0, 1)
        conflict = np.clip(0.24 * stress + 0.24 * burnout + 0.16 * meeting + 0.13 * workload + 0.11 * neighbor_pressure - 0.12 * collaboration - 0.08 * sentiment, 0, 1)
        spread = np.clip(0.28 * burnout + 0.24 * stress + 0.18 * workload + 0.18 * neighbor_pressure + 0.08 * meeting - 0.08 * focus, 0, 1)
        influence = np.clip(0.42 * leadership + 0.2 * collaboration + 0.14 * sentiment + 0.12 * task_completion + 0.12 * productivity, 0, 1)
        targets = np.column_stack([compatibility, conflict, spread, influence]).astype(np.float32)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.018, weight_decay=0.0006)
        criterion = torch.nn.MSELoss()
        feature_tensor = torch.tensor(features)
        adjacency_tensor = torch.tensor(adjacency)
        target_tensor = torch.tensor(targets)
        self.model.train()
        for _ in range(180):
            optimizer.zero_grad()
            loss = criterion(self.model(feature_tensor, adjacency_tensor), target_tensor)
            loss.backward()
            optimizer.step()
        self.model.eval()
        with torch.no_grad():
            predictions = self.model(feature_tensor, adjacency_tensor).numpy()
        mae = float(np.mean(np.abs(predictions - targets)))
        self.metrics_data = {
            "model": self.model_name,
            "training_graph_nodes": int(features.shape[0]),
            "training_graph_edges": int(np.count_nonzero(adjacency) - features.shape[0]),
            "mae": round(mae, 4),
            "embedding_dimensions": 8,
            "features": ",".join(self.feature_names),
        }
        torch.save(self.model.state_dict(), GRAPH_MODEL_PATH)
        METRICS_PATH.write_text(json.dumps(self.metrics_data, indent=2), encoding="utf-8")
        return self.metrics_data

    def infer(self, employees: list[TeamEmployeeProfile], pairs: list[TeamCompatibilityPair]) -> GraphInference:
        if not self.available:
            self.train()
        self.model.eval()
        node_index = {employee.employee_id: index for index, employee in enumerate(employees)}
        features = np.array([self.employee_features(employee) for employee in employees], dtype=np.float32)
        adjacency = np.eye(len(employees), dtype=np.float32)
        edge_lookup: dict[frozenset[str], TeamCompatibilityPair] = {}
        for pair in pairs:
            if pair.source_id not in node_index or pair.target_id not in node_index:
                continue
            source = node_index[pair.source_id]
            target = node_index[pair.target_id]
            weight = np.clip((pair.compatibility_score * 0.56 + pair.collaboration_success_probability * 0.24 + (100 - pair.conflict_probability) * 0.2) / 100, 0.04, 1)
            adjacency[source, target] = weight
            adjacency[target, source] = weight
            edge_lookup[frozenset({pair.source_id, pair.target_id})] = pair
        adjacency = self._normalize_adjacency(adjacency)
        with torch.no_grad():
            feature_tensor = torch.tensor(features)
            adjacency_tensor = torch.tensor(adjacency)
            embeddings = self.model.embed(feature_tensor, adjacency_tensor).numpy()[:, :8]
            predictions = self.model(feature_tensor, adjacency_tensor).numpy()
        nodes = []
        for employee, embedding, output in zip(employees, embeddings, predictions, strict=True):
            nodes.append(
                GraphNodePrediction(
                    employee_id=employee.employee_id,
                    embedding=[round(float(value), 4) for value in embedding],
                    compatibility_projection=round(float(np.clip(output[0] * 100, 0, 100)), 2),
                    conflict_projection=round(float(np.clip(output[1] * 100, 0, 100)), 2),
                    burnout_spread_risk=round(float(np.clip(output[2] * 100, 0, 100)), 2),
                    leadership_influence=round(float(np.clip(output[3] * 100, 0, 100)), 2),
                )
            )
        attention = {}
        for key, pair in edge_lookup.items():
            ids = list(key)
            first = node_index[ids[0]]
            second = node_index[ids[1]]
            similarity = self._cosine(embeddings[first], embeddings[second])
            relationship = (pair.compatibility_score + pair.collaboration_success_probability + (100 - pair.conflict_probability)) / 300
            attention[key] = round(float(np.clip(similarity * 0.46 + relationship * 0.54, 0, 1)), 3)
        return GraphInference(nodes=nodes, edge_attention=attention, metrics=self.metrics_data)

    def employee_features(self, employee: TeamEmployeeProfile) -> list[float]:
        return [
            self._avg(employee.productivity_history, employee.task_completion_rate),
            self._avg(employee.stress_history, employee.burnout_risk),
            (employee.sentiment_trend + 1) / 2,
            employee.task_completion_rate,
            employee.meeting_participation,
            employee.collaboration_frequency,
            employee.leadership_score,
            employee.burnout_risk,
            employee.current_workload,
            employee.focus_ratio,
        ]

    @staticmethod
    def _normalize_adjacency(adjacency: np.ndarray) -> np.ndarray:
        row_sums = adjacency.sum(axis=1, keepdims=True)
        return adjacency / np.clip(row_sums, 1e-6, None)

    @staticmethod
    def _cosine(first: np.ndarray, second: np.ndarray) -> float:
        denom = float(np.linalg.norm(first) * np.linalg.norm(second))
        if denom <= 1e-9:
            return 0.0
        return float((np.dot(first, second) / denom + 1) / 2)

    @staticmethod
    def _avg(values: list[float], fallback: float) -> float:
        return float(np.clip(np.mean(values) if values else fallback, 0, 1))


graph_relation_engine = GraphRelationEngine()
