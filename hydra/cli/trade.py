import typer
from typing import Optional

app = typer.Typer(help="수동 매매 명령 (Phase 1에서 전략 연동)")


@app.command()
def kr(symbol: str, side: str, qty: float):
    """한국 주식 수동 주문."""
    typer.echo(f"[한국주식] {side} {symbol} {qty}주 - Phase 1에서 구현 예정")


@app.command()
def us(symbol: str, side: str, qty: float):
    """미국 주식 수동 주문."""
    typer.echo(f"[미국주식] {side} {symbol} {qty}주 - Phase 1에서 구현 예정")


@app.command()
def crypto(
    exchange: str,
    symbol: str,
    side: str,
    qty: float,
    leverage: int = typer.Option(1, "--leverage", "-l", help="선물 레버리지 배수 (1~125x). 현물은 1로 고정.", min=1, max=125),
    futures: bool = typer.Option(False, "--futures", help="선물 주문 여부"),
):
    """암호화폐 수동 주문. 선물은 --futures --leverage N 으로 레버리지 지정."""
    if futures and leverage > 1:
        typer.echo(f"[{exchange}] {side} {symbol} {qty} x {leverage} 레버리지 (선물) - Phase 1에서 구현 예정")
    elif futures:
        typer.echo(f"[{exchange}] {side} {symbol} {qty} (선물) - Phase 1에서 구현 예정")
    else:
        typer.echo(f"[{exchange}] {side} {symbol} {qty} (현물) - Phase 1에서 구현 예정")


@app.command()
def poly(market_id: str, side: str, amount: float):
    """Polymarket 예측시장 주문."""
    typer.echo(f"[Polymarket] {side} {market_id} ${amount} - Phase 1에서 구현 예정")
