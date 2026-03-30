import typer
import httpx
from hydra.config.settings import get_settings

app = typer.Typer(help="시스템 상태 확인")


@app.callback(invoke_without_command=True)
def status():
    """HYDRA 상태 확인."""
    settings = get_settings()
    try:
        h = httpx.get("http://127.0.0.1:8000/health", timeout=5)
        s = httpx.get(
            "http://127.0.0.1:8000/status",
            headers={"X-HYDRA-KEY": settings.hydra_api_key},
            timeout=5,
        )
        r = httpx.get(
            "http://127.0.0.1:8000/risk",
            headers={"X-HYDRA-KEY": settings.hydra_api_key},
            timeout=5,
        )
        p = httpx.get(
            "http://127.0.0.1:8000/pnl",
            headers={"X-HYDRA-KEY": settings.hydra_api_key},
            timeout=5,
        )
        typer.echo(f"[정상] 서버 상태 정상 | 프로필: {s.json()['profile']} | 가동시간: {h.json()['uptime_seconds']}초")

        risk = r.json()
        ks = "ACTIVE" if risk["kill_switch_active"] else "NORMAL"
        typer.echo(f"Kill Switch: {ks} | 일일 손익(리스크): {risk['daily_pnl_pct']*100:.2f}%")

        pnl = p.json()
        sign = lambda v: "+" if v >= 0 else ""
        typer.echo(
            f"\n=== 손익 현황 ===\n"
            f"  실현 손익 (누적): {sign(pnl['realized_total'])}{pnl['realized_total']:,.4f} USDT\n"
            f"  실현 손익 (오늘): {sign(pnl['daily_realized'])}{pnl['daily_realized']:,.4f} USDT\n"
            f"  미실현 손익:      {sign(pnl['unrealized'])}{pnl['unrealized']:,.4f} USDT\n"
            f"  총 손익:          {sign(pnl['total_pnl'])}{pnl['total_pnl']:,.4f} USDT\n"
            f"  체결 거래 수:      {pnl['trade_count']}건"
        )

        if pnl["positions"]:
            typer.echo("\n  -- 오픈 포지션 --")
            for pos in pnl["positions"]:
                lev = f" {pos['leverage']}x" if pos.get("leverage", 1) > 1 else ""
                upnl = pos.get("unrealized_pnl", 0)
                typer.echo(
                    f"  [{pos['market']}] {pos['symbol']} {pos['side'].upper()}{lev} "
                    f"  수량: {pos['qty']}  평균단가: {pos['avg_price']}  "
                    f"미실현: {sign(upnl)}{upnl:,.4f}"
                )
        else:
            typer.echo("\n  오픈 포지션 없음")

    except httpx.ConnectError:
        typer.echo("[오류] 서버 오프라인")
