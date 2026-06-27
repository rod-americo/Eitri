"""Schemas Pydantic para YAMLs de experimento e contratos externos."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ExperimentBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    owner_user: str
    task: str
    domain: str
    objective: str
    output_mode: str = "structured"
    generate_text: bool = False

    @field_validator("output_mode")
    @classmethod
    def require_structured_output(cls, value: str) -> str:
        if value != "structured":
            raise ValueError("O experimento inicial deve usar saída estruturada.")
        return value

    @field_validator("generate_text")
    @classmethod
    def forbid_text_generation(cls, value: bool) -> bool:
        if value:
            raise ValueError("O experimento inicial não pode gerar texto.")
        return value


class DatasetPairing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_delta_hours: int = Field(gt=0, le=24)
    patient_level: bool = True


class DatasetSplit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: str = "patient"
    train: float
    validation: float
    test: float

    @field_validator("strategy")
    @classmethod
    def require_patient_strategy(cls, value: str) -> str:
        if value != "patient":
            raise ValueError("O split deve ser por paciente.")
        return value

    @model_validator(mode="after")
    def require_sum_one(self) -> DatasetSplit:
        total = self.train + self.validation + self.test
        if abs(total - 1.0) > 0.0001:
            raise ValueError("As frações de split devem somar 1.0.")
        return self


class DatasetLabels(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: str = "structured"
    require_integrity_check: bool = True


class DatasetBlock(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    version: str
    pairing: DatasetPairing
    split: DatasetSplit
    labels: DatasetLabels


class MetricsBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary: str
    secondary: list[str] = Field(default_factory=list)


class ExperimentYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment: ExperimentBlock
    dataset: DatasetBlock
    metrics: MetricsBlock
    guardrails: dict[str, Any]


def load_experiment_yaml(path: str | Path) -> ExperimentYaml:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    return ExperimentYaml.model_validate(raw)
