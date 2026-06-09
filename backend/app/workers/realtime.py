from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

import redis.asyncio as redis

from app.core.config import settings
from app.services.alert_service import alert_service
from app.services.platform_service import platform_service
from app.services.strategic_intelligence_service import strategic_intelligence_service
from app.services.suggestion_service import smart_suggestion_service


LOGGER = logging.getLogger("nexusmind.realtime-worker")
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SNAPSHOT_PATH = DATA_DIR / "realtime_worker_snapshots.jsonl"
_LOCK = Lock()


def build_snapshot() -> dict[str, Any]:
    platform = platform_service.operating_system()
    alerts = alert_service.feed()
    suggestions = smart_suggestion_service.generate()
    strategic = strategic_intelligence_service.analyze()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stream": "nexusmind.enterprise.realtime",
        "platform": {
            "score": platform.summary.platform_score,
            "capabilities": platform.summary.total_capabilities,
            "ready": platform.summary.ready,
            "realtime_streams": platform.summary.realtime_streams,
        },
        "alerts": {
            "count": len(alerts.alerts),
            "critical": sum(1 for alert in alerts.alerts if alert.severity == "critical"),
            "top": alerts.alerts[0].model_dump(mode="json") if alerts.alerts else None,
        },
        "suggestions": {
            "count": len(suggestions.suggestions),
            "top": suggestions.suggestions[0].model_dump(mode="json") if suggestions.suggestions else None,
        },
        "strategic": {
            "competitors": len(strategic.competitive_intelligence),
            "clients": len(strategic.client_relationship_intelligence),
            "marketplace_matches": len(strategic.internal_marketplace_matches),
            "crisis_severity": strategic.crisis_response.risk_level,
            "innovation_signals": len(strategic.innovation_signals),
        },
    }


def persist_snapshot(snapshot: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with SNAPSHOT_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(snapshot, default=str) + "\n")


async def publish_snapshot(snapshot: dict[str, Any]) -> None:
    client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    try:
        await asyncio.wait_for(
            client.publish("nexusmind.realtime.snapshots", json.dumps(snapshot, default=str)),
            timeout=1.5,
        )
    finally:
        await client.aclose()


async def run_once(publish: bool = True) -> dict[str, Any]:
    snapshot = build_snapshot()
    persist_snapshot(snapshot)
    if publish:
        try:
            await publish_snapshot(snapshot)
        except Exception as exc:  # pragma: no cover - depends on external Redis availability.
            LOGGER.warning("Redis publish skipped: %s", exc)
    return snapshot


async def run_forever(interval_seconds: float, publish: bool) -> None:
    while True:
        snapshot = await run_once(publish=publish)
        LOGGER.info(
            "snapshot score=%s capabilities=%s alerts=%s",
            snapshot["platform"]["score"],
            snapshot["platform"]["capabilities"],
            snapshot["alerts"]["count"],
        )
        await asyncio.sleep(interval_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the NEXUSMIND realtime intelligence worker.")
    parser.add_argument("--once", action="store_true", help="Generate one realtime snapshot and exit.")
    parser.add_argument("--interval", type=float, default=5.0, help="Loop interval in seconds.")
    parser.add_argument("--no-publish", action="store_true", help="Skip Redis publish and only persist snapshots.")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = parse_args()
    publish = not args.no_publish
    if args.once:
        snapshot = asyncio.run(run_once(publish=publish))
        print(json.dumps(snapshot, default=str))
        return
    asyncio.run(run_forever(interval_seconds=max(args.interval, 1.0), publish=publish))


if __name__ == "__main__":
    main()
