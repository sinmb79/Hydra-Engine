#!/usr/bin/env python3
"""HYDRA 하드웨어 벤치마크."""
import time
import math
import typer
import psutil


def cpu_benchmark(seconds: int = 3) -> float:
    """단순 연산 벤치마크. ops/sec 반환."""
    count = 0
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        math.sqrt(2 ** 32)
        count += 1
    return count / seconds


def main(profile: str = "lite"):
    typer.echo(f"🔬 벤치마크 시작 (프로필: {profile})")
    mem = psutil.virtual_memory()
    typer.echo(f"  RAM: {mem.total // 1024**3}GB  사용 가능: {mem.available // 1024**3}GB")

    ops = cpu_benchmark(2)
    typer.echo(f"  CPU 연산: {ops/1e6:.1f}M ops/sec")

    thresholds = {"lite": 50, "pro": 100, "expert": 200}
    min_ops = thresholds.get(profile, 50) * 1e6
    if ops >= min_ops:
        typer.echo(f"  ✅ 벤치마크 통과")
    else:
        typer.echo(f"  ⚠️  성능 미달 (권장: {min_ops/1e6:.0f}M ops/sec)")


if __name__ == "__main__":
    typer.run(main)
