from auditize.scheduler import build_scheduler


def test_build_scheduler():
    assert build_scheduler() is not None
