# Configure different hypothesis profiles
import os

from hypothesis import HealthCheck, Phase, settings

FAST_PROFILE = "fast"
CI_PROFILE = "ci"


# 'fast' profile for local development
settings.register_profile(
    FAST_PROFILE,
    # Set to true for test reproducibility
    # https://hypothesis.readthedocs.io/en/latest/settings.html#hypothesis.settings.derandomize
    derandomize=False,
    max_examples=3,
    # https://hypothesis.readthedocs.io/en/latest/settings.html#controlling-what-runs
    phases=[Phase.generate, Phase.explain],
    # (sblaisdo) fails `HealthCheck.too_slow` with initial schema/addon loading
    suppress_health_check=[HealthCheck.too_slow],
    # (sblaisdo) default deadline of 200ms is exceeded in some cases
    deadline=None,
)

# 'ci' profile for pr_check.sh
settings.register_profile(
    CI_PROFILE,
    derandomize=False,
    max_examples=5,
    phases=[Phase.generate, Phase.explain],
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)

# Load profile
p = CI_PROFILE if os.getenv("CI") == "true" else FAST_PROFILE
print(f"Loading hypothesis profile: {p}")
settings.load_profile(p)
