"""Smoke test: verify core modules are importable."""


def test_imports():
    import config  # noqa: F401
    import db  # noqa: F401
    import features  # noqa: F401
    import fetcher  # noqa: F401
    import monitor  # noqa: F401
    import trader  # noqa: F401
