import sys
import psutil
import typer
from pathlib import Path

from hydra.config.keys import KeyManager
from hydra.config.markets import MarketManager
from hydra.logging.setup import configure_logging


MARKETS = {
    "kr": "한국 주식 (KIS)",
    "us": "미국 주식 (KIS)",
    "upbit": "업비트 (암호화폐)",
    "binance": "바이낸스 (암호화폐)",
    "hl": "Hyperliquid ([주의] 고위험)",
    "poly": "Polymarket 예측시장 ([주의] 고위험)",
}


def detect_hardware() -> dict:
    return {
        "cpu_cores": psutil.cpu_count(logical=False),
        "ram_gb": round(psutil.virtual_memory().total / 1024**3),
        "disk_gb": round(psutil.disk_usage("/").total / 1024**3),
    }


def recommend_profile(hw: dict) -> str:
    if hw["ram_gb"] >= 32 and hw["cpu_cores"] >= 16:
        return "expert"
    elif hw["ram_gb"] >= 16 and hw["cpu_cores"] >= 8:
        return "pro"
    return "lite"


def run_setup():
    """7단계 HYDRA 초기 설정 위자드."""
    configure_logging()
    typer.echo("\nHYDRA 설정 위자드에 오신 것을 환영합니다.\n")

    # Step 1: 하드웨어 감지
    typer.echo("-- Step 1/7: 하드웨어 감지 --")
    hw = detect_hardware()
    typer.echo(f"  CPU: {hw['cpu_cores']}코어  RAM: {hw['ram_gb']}GB  Disk: {hw['disk_gb']}GB")

    # Step 2: 프로필 추천
    typer.echo("\n-- Step 2/7: 프로필 선택 --")
    recommended = recommend_profile(hw)
    typer.echo(f"  추천 프로필: {recommended.upper()}")
    profile = typer.prompt("  프로필 선택 [lite/pro/expert]", default=recommended)
    if profile not in ("lite", "pro", "expert"):
        typer.echo("[오류] 잘못된 프로필입니다. lite, pro, expert 중 선택하세요.")
        raise typer.Exit(1)

    # Step 3: AI 선택
    typer.echo("\n-- Step 3/7: AI 모드 선택 --")
    typer.echo("  [1] OFF (규칙 기반만)  [2] 경량 CPU  [3] GPU  [4] 커스텀")
    ai_choice = typer.prompt("  선택", default="1")
    ai_mode = {"1": "off", "2": "cpu", "3": "gpu", "4": "custom"}.get(ai_choice, "off")

    # Step 4: 인터페이스
    typer.echo("\n-- Step 4/7: 인터페이스 선택 --")
    typer.echo("  [1] CLI+Telegram  [2] Dashboard+Telegram  [3] 전부  [4] Telegram만")
    interface = typer.prompt("  선택", default="1")

    # Step 5: 면책조항 동의
    typer.echo("\n-- Step 5/7: 면책조항 동의 --")
    disclaimer = Path("DISCLAIMER.md").read_text(encoding="utf-8") if Path("DISCLAIMER.md").exists() else ""
    typer.echo(disclaimer)
    accepted = typer.confirm("\n위 면책조항에 동의하십니까?")
    if not accepted:
        typer.echo("면책조항에 동의하지 않으면 설치를 진행할 수 없습니다.")
        sys.exit(1)

    # Step 5b: 시장 선택 + API 키
    typer.echo("\n-- 시장 선택 --")
    selected_markets = []
    mm = MarketManager()
    km = KeyManager()

    for market_id, label in MARKETS.items():
        if typer.confirm(f"  {label} 사용?", default=False):
            selected_markets.append(market_id)
            mode = typer.prompt(f"  {label} 모드 [paper/live]", default="paper")
            mm.enable(market_id, mode)

            if market_id in ("kr", "us"):
                app_key = typer.prompt(f"  KIS App Key ({label})", hide_input=True)
                secret = typer.prompt(f"  KIS App Secret ({label})", hide_input=True)
                km.store(f"kis_{market_id}", app_key, secret)
                account_no = typer.prompt("  KIS 계좌번호 (예: 50123456-01)")
                km.store("kis_account", account_no, "")
            elif market_id in ("upbit", "binance", "hl"):
                api_key = typer.prompt(f"  {label} API Key", hide_input=True)
                secret = typer.prompt(f"  {label} Secret", hide_input=True)
                km.store(market_id, api_key, secret)

    # Step 6: 벤치마크
    typer.echo("\n-- Step 6/7: 성능 벤치마크 실행 --")
    typer.echo("  (잠시 기다려 주세요...)")
    import subprocess
    try:
        subprocess.run(["python", "scripts/benchmark.py", "--profile", profile], timeout=30)
    except Exception:
        typer.echo("  벤치마크 스킵 (scripts/benchmark.py 없음)")

    # Step 7: 설정 저장
    typer.echo("\n-- Step 7/7: 설정 완료 --")
    env_content = f"""HYDRA_PROFILE={profile}
HYDRA_API_KEY={_generate_api_key()}
REDIS_URL=redis://localhost:6379
"""
    Path(".env").write_text(env_content)
    typer.echo("\n[완료] 설정이 저장되었습니다.")
    typer.echo(f"   프로필: {profile.upper()}  |  AI: {ai_mode}  |  시장: {', '.join(selected_markets) or '없음'}")
    typer.echo("   hydra start 또는 docker compose -f docker-compose.lite.yml up 으로 시작하세요.")


def _generate_api_key() -> str:
    import secrets
    return secrets.token_urlsafe(32)
