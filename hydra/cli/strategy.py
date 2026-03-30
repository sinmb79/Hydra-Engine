import typer

app = typer.Typer(help="전략 관리 (Phase 2에서 구현)")


@app.command()
def list_strategies():
    typer.echo("전략 목록 - Phase 2에서 구현 예정")


@app.command()
def start(name: str):
    typer.echo(f"전략 시작: {name} - Phase 2에서 구현 예정")


@app.command()
def stop(name: str):
    typer.echo(f"전략 중지: {name} - Phase 2에서 구현 예정")
