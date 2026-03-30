from dataclasses import dataclass


@dataclass
class ProfileLimits:
    name: str
    core_mem_gb: int
    redis_mem_gb: int
    db_mem_gb: int
    cpus: int
    ai_enabled: bool
    db_backend: str  # "sqlite" or "timescaledb"


PROFILES: dict[str, ProfileLimits] = {
    "lite": ProfileLimits(
        name="lite",
        core_mem_gb=2,
        redis_mem_gb=1,
        db_mem_gb=0,
        cpus=2,
        ai_enabled=False,
        db_backend="sqlite",
    ),
    "pro": ProfileLimits(
        name="pro",
        core_mem_gb=4,
        redis_mem_gb=2,
        db_mem_gb=4,
        cpus=4,
        ai_enabled=True,
        db_backend="timescaledb",
    ),
    "expert": ProfileLimits(
        name="expert",
        core_mem_gb=8,
        redis_mem_gb=4,
        db_mem_gb=8,
        cpus=8,
        ai_enabled=True,
        db_backend="timescaledb",
    ),
}


def get_profile(name: str) -> ProfileLimits:
    if name not in PROFILES:
        raise ValueError(f"Unknown profile '{name}'. Choose: {list(PROFILES)}")
    return PROFILES[name]
