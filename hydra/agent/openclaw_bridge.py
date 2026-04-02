"""
HYDRA ↔ OpenClaw 브리지.

호스트에서 직접 실행하는 서비스. Docker 외부에서 Redis에 접근하고
openclaw CLI를 subprocess로 호출해 분석 결과를 Redis에 저장.

실행: python -m hydra.agent.openclaw_bridge
"""
import asyncio
import json
import os
import shutil
import subprocess
import sys
import time

import redis

from hydra.agent.report_writer import write_report

REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")
OPENCLAW_AGENT_ID = os.environ.get("OPENCLAW_AGENT_ID", "main")
OPENCLAW_TIMEOUT = int(os.environ.get("OPENCLAW_TIMEOUT", "30"))
POLL_INTERVAL = int(os.environ.get("OPENCLAW_POLL_INTERVAL", "300"))  # 5분

_RESULT_KEY = "hydra:openclaw:analysis:latest"
_SENTIMENT_KEY_PREFIX = "hydra:openclaw:sentiment"

SYSTEM_PROMPT = """You are the OpenClaw financial analysis agent integrated into the HYDRA trading engine.
Your role is strictly read-only: analyze market state and provide structured JSON output.
You CANNOT place orders, modify positions, or take any trading action.
Respond ONLY with valid JSON matching the schema provided. No extra text."""

ANALYSIS_PROMPT_TEMPLATE = """Analyze the following HYDRA trading engine state and return a JSON report.

## Current Market State
{state_json}

## Required JSON Output Schema
{{
  "sentiment": {{
    "<market>:<symbol>": {{
      "score": <float -1.0 to 1.0>,
      "reasoning": "<brief explanation>",
      "confidence": <float 0.0 to 1.0>
    }}
  }},
  "regime_assessment": {{
    "<market>:<symbol>:<timeframe>": {{
      "assessment": "<agrees|disagrees|neutral>",
      "note": "<brief note>"
    }}
  }},
  "alerts": [
    {{
      "level": "<INFO|WARN|CRITICAL>",
      "message": "<Korean language alert text>",
      "market": "<market or null>"
    }}
  ],
  "rationale": "<overall 1-2 sentence trade rationale in Korean>",
  "risk_flags": ["<flag1>", "<flag2>"]
}}

Constraints:
- Max 30s to generate
- Sentiment score must use decay-weighted analysis (recent news >> old news)
- Flag any P(bear) > 0.7 signals as WARN or CRITICAL
- Alerts must be in Korean
"""


_SUMMARY_TIMEFRAMES = {"1h", "4h", "1d"}


def _collect_hydra_state(r: redis.Redis) -> dict:
    """Redis에서 현재 HYDRA 상태를 수집. 주요 타임프레임만 포함."""
    state = {
        "signals": {},
        "regimes": {},
        "indicators_summary": {},
        "sentiment": {},
        "positions": [],
        "collected_at": int(time.time() * 1000),
    }

    # 시그널 (주요 타임프레임만)
    for key in r.keys("hydra:signal:*"):
        raw = r.get(key)
        if raw:
            parts = key.split(":")
            tf = parts[-1]
            if tf not in _SUMMARY_TIMEFRAMES:
                continue
            label = ":".join(parts[2:])
            state["signals"][label] = json.loads(raw)

    # 레짐 (주요 타임프레임만)
    for key in r.keys("hydra:regime:*"):
        raw = r.get(key)
        if raw:
            parts = key.split(":")
            tf = parts[-1]
            if tf not in _SUMMARY_TIMEFRAMES:
                continue
            label = ":".join(parts[2:])
            state["regimes"][label] = json.loads(raw)

    # 기존 감성 점수
    for key in r.keys("hydra:sentiment:*"):
        raw = r.get(key)
        if raw:
            symbol = key.split(":")[-1]
            state["sentiment"][symbol] = json.loads(raw)

    # 지표 요약 (주요 타임프레임, 핵심 지표만)
    for key in r.keys("hydra:indicator:*"):
        raw = r.get(key)
        if raw:
            parts = key.split(":")
            tf = parts[-1]
            if tf not in _SUMMARY_TIMEFRAMES:
                continue
            label = ":".join(parts[2:])
            data = json.loads(raw)
            state["indicators_summary"][label] = {
                k: v for k, v in data.items()
                if k in ("RSI_14", "ADX_14", "EMA_9", "EMA_20", "close")
            }

    # 포지션
    for key in r.keys("hydra:position:*"):
        raw = r.get(key)
        if raw:
            state["positions"].append(json.loads(raw))

    return state


def _resolve_openclaw() -> tuple[str, list[str]]:
    """openclaw 실행 명령을 반환. (실행파일, 접두 인수) 튜플.

    Windows에서 .cmd 래퍼는 cmd.exe의 8K 명령줄 제한에 걸리므로,
    내부의 node + .mjs 경로를 직접 반환한다.
    """
    for name in ("openclaw", "openclaw.cmd"):
        path = shutil.which(name)
        if path:
            break
    else:
        raise FileNotFoundError("openclaw CLI not found in PATH")

    # Windows .cmd → node + .mjs 직접 호출로 우회
    if sys.platform == "win32" and path.lower().endswith(".cmd"):
        npm_dir = os.path.dirname(path)
        mjs = os.path.join(npm_dir, "node_modules", "openclaw", "openclaw.mjs")
        if os.path.isfile(mjs):
            node = shutil.which("node")
            if node:
                return node, [mjs]
    return path, []


def _call_openclaw(prompt: str) -> dict | None:
    """openclaw agent CLI를 호출해 JSON 응답을 반환."""
    try:
        exe, prefix_args = _resolve_openclaw()
    except FileNotFoundError:
        print("[openclaw] openclaw CLI not found in PATH")
        return None

    try:
        result = subprocess.run(
            [exe, *prefix_args, "agent",
             "--agent", OPENCLAW_AGENT_ID,
             "--message", prompt,
             "--json",
             "--timeout", str(OPENCLAW_TIMEOUT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=OPENCLAW_TIMEOUT + 10,
        )
        if result.returncode != 0:
            print(f"[openclaw] error: {result.stderr[:200]}")
            return None

        output = result.stdout.strip()
        # openclaw --json 출력에서 응답 텍스트 추출
        outer = json.loads(output)
        # 실제 응답 형식: {"result": {"payloads": [{"text": "..."}]}}
        payloads = outer.get("result", {}).get("payloads", [])
        text = payloads[0].get("text", "") if payloads else (
            outer.get("text") or outer.get("reply") or outer.get("message") or output
        )

        # 응답 텍스트에서 JSON 블록 추출
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        return json.loads(text)

    except subprocess.TimeoutExpired:
        print("[openclaw] timeout")
        return None
    except json.JSONDecodeError as e:
        print(f"[openclaw] JSON parse error: {e}")
        return None


def _store_results(r: redis.Redis, analysis: dict) -> None:
    """분석 결과를 Redis에 저장."""
    ts = int(time.time() * 1000)
    analysis["ts"] = ts

    # 전체 분석 최신 결과
    r.set(_RESULT_KEY, json.dumps(analysis))
    r.expire(_RESULT_KEY, 3600)  # 1시간 TTL

    # 심볼별 감성 점수 덮어쓰기
    for key, val in analysis.get("sentiment", {}).items():
        r.set(f"{_SENTIMENT_KEY_PREFIX}:{key}", json.dumps(val))

    # 리포트 파일 저장
    write_report(analysis)


def _send_telegram_alerts(r: redis.Redis, alerts: list[dict]) -> None:
    """WARN/CRITICAL 알림을 Telegram pub/sub 채널에 발행."""
    for alert in alerts:
        if alert.get("level") in ("WARN", "CRITICAL"):
            r.publish("hydra:telegram:alert", json.dumps(alert))


def run_once(r: redis.Redis) -> None:
    print("[openclaw] 상태 수집 중...")
    state = _collect_hydra_state(r)

    if not state["signals"] and not state["regimes"]:
        print("[openclaw] 시그널/레짐 데이터 없음, 건너뜀")
        return

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        state_json=json.dumps(state, ensure_ascii=False, indent=2)
    )

    print("[openclaw] 분석 요청 중...")
    analysis = _call_openclaw(prompt)

    if analysis is None:
        print("[openclaw] 분석 실패")
        return

    _store_results(r, analysis)
    _send_telegram_alerts(r, analysis.get("alerts", []))

    rationale = analysis.get("rationale", "")
    flags = analysis.get("risk_flags", [])
    print(f"[openclaw] 완료 — {rationale[:80]} | 리스크: {flags}")


def main() -> None:
    print(f"[openclaw] 브리지 시작 (agent={OPENCLAW_AGENT_ID}, interval={POLL_INTERVAL}s)")
    r = redis.from_url(REDIS_URL, decode_responses=True)

    while True:
        try:
            run_once(r)
        except Exception as e:
            print(f"[openclaw] 오류: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
