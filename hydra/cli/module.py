import typer

app = typer.Typer(help="AI 모듈 관리")

MODULES = ["regime_detection", "signal_scoring", "feature_selection", "adaptive_retrain",
           "crash_detection", "dynamic_sizing", "sentiment"]


@app.command()
def enable(name: str):
    if name not in MODULES:
        typer.echo(f"[오류] 알 수 없는 모듈: {name}. 사용 가능: {MODULES}")
        raise typer.Exit(1)
    typer.echo(f"모듈 활성화: {name} - Phase 1에서 구현 예정")


@app.command()
def disable(name: str):
    typer.echo(f"모듈 비활성화: {name} - Phase 1에서 구현 예정")


@app.command()
def list_modules():
    typer.echo("AI 모듈 목록:\n" + "\n".join(f"  - {m}" for m in MODULES))
