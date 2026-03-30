import typer
from hydra.config.markets import MarketManager

app = typer.Typer(help="시장 활성화/비활성화")


@app.command()
def enable(market: str, mode: str = typer.Option("paper", help="paper / live")):
    """시장 활성화."""
    mm = MarketManager()
    mm.enable(market, mode)
    typer.echo(f"[완료] {market} 활성화 ({mode} 모드)")


@app.command()
def disable(market: str):
    """시장 비활성화."""
    mm = MarketManager()
    mm.disable(market)
    typer.echo(f"[완료] {market} 비활성화")


@app.command()
def list_markets():
    """활성화된 시장 목록."""
    mm = MarketManager()
    active = mm.get_active_markets()
    if active:
        typer.echo("활성 시장: " + ", ".join(active))
    else:
        typer.echo("활성화된 시장 없음. 'hydra market enable <market>'로 활성화하세요.")
