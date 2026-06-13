from app.services.llm_cost_control import enforce_prompt_limit, enforce_token_limit
from app.utils.url_safety import validate_external_resume_url


def test_validate_external_resume_url_rejects_localhost() -> None:
    try:
        validate_external_resume_url("https://localhost/resume.pdf", validate_dns=False)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected localhost URL to be rejected")


def test_validate_external_resume_url_accepts_public_https() -> None:
    url = "https://example.com/files/resume.pdf"
    validated = validate_external_resume_url(url, validate_dns=False)
    assert validated == url


def test_enforce_prompt_limit_truncates() -> None:
    prompt = "x" * 25
    assert enforce_prompt_limit(prompt, max_chars=10) == "x" * 10


def test_enforce_token_limit_caps_requested_tokens() -> None:
    assert enforce_token_limit(requested=5000, cap=1000) == 1000
    assert enforce_token_limit(requested=0, cap=1000) == 1