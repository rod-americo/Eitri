import pytest
from pydantic import ValidationError

from eitri.schemas import ExperimentYaml, load_experiment_yaml


def test_initial_experiment_yaml_is_valid() -> None:
    parsed = load_experiment_yaml("configs/experiments/chest_xray_ct_24h.yaml")

    assert parsed.experiment.output_mode == "structured"
    assert parsed.experiment.generate_text is False
    assert parsed.dataset.pairing.max_delta_hours == 24
    assert parsed.dataset.split.strategy == "patient"


def test_experiment_yaml_rejects_text_generation() -> None:
    with pytest.raises(ValidationError):
        ExperimentYaml.model_validate(
            {
                "experiment": {
                    "name": "bad",
                    "owner_user": "rodrigo",
                    "task": "bad",
                    "domain": "radiology",
                    "objective": "bad",
                    "output_mode": "structured",
                    "generate_text": True,
                },
                "dataset": {
                    "name": "d",
                    "version": "1",
                    "pairing": {"max_delta_hours": 24, "patient_level": True},
                    "split": {"strategy": "patient", "train": 0.7, "validation": 0.2, "test": 0.1},
                    "labels": {"format": "structured", "require_integrity_check": True},
                },
                "metrics": {"primary": "auroc", "secondary": []},
                "guardrails": {},
            }
        )
