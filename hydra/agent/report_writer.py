"""OpenClaw 분석 결과를 구조화된 로그로 저장."""
import json
import time
from pathlib import Path

LOG_DIR = Path("data/openclaw_reports")


def write_report(report: dict) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    path = LOG_DIR / f"report_{ts}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
