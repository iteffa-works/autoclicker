from app.services.update_service import UpdateService


def test_is_newer_than_string_semver_like() -> None:
    assert UpdateService.is_newer_than("0.1.0", "1.0.0") is True
    assert UpdateService.is_newer_than("1.0.0", "1.0.0") is False
