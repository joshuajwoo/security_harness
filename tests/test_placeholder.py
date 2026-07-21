"""Placeholder test to ensure pytest exits 0 with a clean setup."""


def test_project_imports():
    """Verify core packages are importable."""
    import agents
    import scenarios
    import harness
    import harness.grading

    assert agents is not None
    assert scenarios is not None
    assert harness is not None
    assert harness.grading is not None
