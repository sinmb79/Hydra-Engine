#!/usr/bin/env python3
"""
AWS Lambda 배포용 DR L2 워치독.
1분마다 헬스체크. 3회 연속 실패 시 비상 청산 API 호출.
"""
import os
import json
import boto3
import requests

HEALTH_URL = os.environ.get("HYDRA_HEALTH_URL", "http://YOUR_MINI_PC_IP:8000/health")
KILL_URL = os.environ.get("HYDRA_KILL_URL", "http://YOUR_MINI_PC_IP:8000/killswitch")
HYDRA_API_KEY = os.environ.get("HYDRA_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
MAX_FAILURES = 3
FAILURE_KEY = "hydra_watchdog_failures"


def get_failure_count() -> int:
    dynamo = boto3.resource("dynamodb")
    table = dynamo.Table("hydra_watchdog")
    resp = table.get_item(Key={"id": FAILURE_KEY})
    return int(resp.get("Item", {}).get("count", 0))


def set_failure_count(count: int) -> None:
    dynamo = boto3.resource("dynamodb")
    table = dynamo.Table("hydra_watchdog")
    table.put_item(Item={"id": FAILURE_KEY, "count": count})


def reset_failure_count() -> None:
    set_failure_count(0)


def emergency_close_all() -> dict:
    resp = requests.post(
        KILL_URL,
        params={"reason": "dr_l2_watchdog"},
        headers={"X-HYDRA-KEY": HYDRA_API_KEY},
        timeout=30,
    )
    return resp.json()


def send_telegram_alert(message: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10)


def lambda_handler(event, context) -> dict:
    failure_count = get_failure_count()
    try:
        r = requests.get(HEALTH_URL, timeout=5)
        if r.status_code == 200:
            reset_failure_count()
            return {"status": "ok", "failures": 0}
    except Exception:
        pass

    failure_count += 1
    set_failure_count(failure_count)

    if failure_count >= MAX_FAILURES:
        result = emergency_close_all()
        send_telegram_alert(f"⚠️ DR L2 발동: 미니PC {MAX_FAILURES}회 무응답.\n전 포지션 청산: {result}")
        reset_failure_count()

    return {"status": "failure", "failures": failure_count}
