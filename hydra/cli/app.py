import typer
from hydra.cli import kill, status, trade, market, strategy, module
from hydra.cli import setup_wizard

app = typer.Typer(name="hydra", help="HYDRA 자동매매 시스템")
app.add_typer(kill.app, name="kill")
app.add_typer(status.app, name="status")
app.add_typer(trade.app, name="trade")
app.add_typer(market.app, name="market")
app.add_typer(strategy.app, name="strategy")
app.add_typer(module.app, name="module")

app.command("setup")(setup_wizard.run_setup)

if __name__ == "__main__":
    app()
