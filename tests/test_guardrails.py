from eitri.config import EitriConfig, GuardrailConfig
from eitri.guardrails import (
    RunIntent,
    evaluate_guardrails,
    guardrails_pass,
    validate_destructive_confirmation,
)


def test_remote_execution_requires_dry_run() -> None:
    config = EitriConfig(
        guardrails=GuardrailConfig(
            require_git_commit=False,
            require_dataset_hash=False,
            require_config_hash=False,
            require_dry_run_before_remote=True,
        )
    )
    results = evaluate_guardrails(
        RunIntent(name="remote", target_host="thor", dry_run=False),
        config,
    )

    assert guardrails_pass(results) is False
    assert any(result.name == "remote_dry_run" and not result.passed for result in results)


def test_destructive_confirmation_must_match_literal_phrase() -> None:
    config = EitriConfig()

    assert validate_destructive_confirmation("no", config).passed is False
    assert validate_destructive_confirmation("CONFIRMAR EXCLUSÃO", config).passed is True
