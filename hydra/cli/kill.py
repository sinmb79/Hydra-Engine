import asyncio
import typer
import httpx
from hydra.config.settings import get_settings

app = typer.Typer(help="Kill Switch - 전 포지션 즉시 청산")


@app.callback(invoke_without_command=True)
def kill(reason: str = typer.Option("cli_manual", help="청산 사유")):
    """전 포지션 즉시 시장가 청산."""
    confirm = typer.confirm("[주의] 전 포지션을 청산합니다. 계속하시겠습니까?")
    if not confirm:
        typer.echo("취소됨.")
        raise typer.Exit()

    settings = get_settings()
    try:
        resp = httpx.post(
            "http://127.0.0.1:8000/killswitch",
            params={"reason": reason},
            headers={"X-HYDRA-KEY": settings.hydra_api_key},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        typer.echo(f"[완료] Kill Switch 실행. 청산: {len(data.get('closed', []))}개")
    except httpx.ConnectError:
        typer.echo("[오류] HYDRA 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        raise typer.Exit(1)
