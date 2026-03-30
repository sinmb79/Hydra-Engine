import pytest
from hydra.config.profiles import get_profile


def test_lite_profile_has_memory_limits():
    profile = get_profile("lite")
    assert profile.core_mem_gb <= 4
    assert profile.redis_mem_gb <= 2


def test_expert_profile_higher_than_lite():
    lite = get_profile("lite")
    expert = get_profile("expert")
    assert expert.core_mem_gb > lite.core_mem_gb


def test_invalid_profile_raises():
    with pytest.raises(ValueError, match="Unknown profile"):
        get_profile("invalid")


def test_lite_no_ai():
    profile = get_profile("lite")
    assert profile.ai_enabled is False


def test_pro_expert_have_ai():
    for name in ("pro", "expert"):
        assert get_profile(name).ai_enabled is True
