"""Contratos de plugins para datasets, modelos, tarefas, métricas, avaliação e exportação."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable

from eitri.schemas import ExperimentYaml

PluginKind = Literal["dataset", "model", "task", "metrics", "evaluation", "exporter"]
REQUIRED_PLUGIN_KINDS: tuple[PluginKind, ...] = (
    "dataset",
    "model",
    "task",
    "metrics",
    "evaluation",
    "exporter",
)


@dataclass(frozen=True)
class PluginCapability:
    kind: PluginKind
    name: str
    contract: str
    description: str = ""


@dataclass(frozen=True)
class PluginDescriptor:
    name: str
    version: str
    source: str
    description: str
    capabilities: tuple[PluginCapability, ...] = ()

    @property
    def kinds(self) -> tuple[PluginKind, ...]:
        return tuple(capability.kind for capability in self.capabilities)


@runtime_checkable
class EitriPlugin(Protocol):
    name: str
    version: str

    def describe(self) -> str:
        """Retorna descrição humana do plugin."""

    def capabilities(self) -> tuple[PluginCapability, ...]:
        """Declara capacidades fornecidas pelo plugin."""


@runtime_checkable
class DatasetPlugin(EitriPlugin, Protocol):
    def validate_dataset(self, experiment: ExperimentYaml) -> list[str]:
        """Valida o contrato de dataset para um experimento."""


@runtime_checkable
class ModelPlugin(EitriPlugin, Protocol):
    def model_contract(self) -> dict[str, Any]:
        """Retorna contrato do modelo sem instanciar treinamento pesado."""


@runtime_checkable
class TaskPlugin(EitriPlugin, Protocol):
    def validate_task(self, experiment: ExperimentYaml) -> list[str]:
        """Valida contrato da tarefa."""


@runtime_checkable
class MetricsPlugin(EitriPlugin, Protocol):
    def metric_names(self) -> tuple[str, ...]:
        """Lista métricas produzidas pelo plugin."""


@runtime_checkable
class EvaluationPlugin(EitriPlugin, Protocol):
    def evaluation_contract(self) -> dict[str, Any]:
        """Declara como a avaliação será executada e persistida."""


@runtime_checkable
class ExporterPlugin(EitriPlugin, Protocol):
    def artifact_types(self) -> tuple[str, ...]:
        """Lista tipos de artefato exportáveis."""


@dataclass(frozen=True)
class PluginValidation:
    plugin_name: str
    missing_kinds: tuple[PluginKind, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return not self.missing_kinds and not self.errors


class ChestXrayCt24hPlugin:
    """Plugin de referência para radiografia de tórax pareada com TC em até 24h."""

    name = "radiology-chest-xray-ct-24h"
    version = "0.1.0"

    def describe(self) -> str:
        return (
            "Dataset/tarefa estruturada para radiografia de tórax em leito "
            "pareada com TC até 24h."
        )

    def capabilities(self) -> tuple[PluginCapability, ...]:
        return (
            PluginCapability(
                kind="dataset",
                name="bedside-chest-xray-ct-24h",
                contract="paired_imaging_dataset",
                description="Pareamento CR -> CT em janela de 24 horas com split por paciente.",
            ),
            PluginCapability(
                kind="task",
                name="paired_imaging_structured_prediction",
                contract="structured_output_no_text_generation",
                description="Predição estruturada sem geração de texto.",
            ),
            PluginCapability(
                kind="model",
                name="structured-radiology-baseline",
                contract="model_factory_placeholder",
                description="Factory futura para modelos de baseline estruturado.",
            ),
            PluginCapability(
                kind="metrics",
                name="radiology-structured-metrics",
                contract="classification_and_calibration_metrics",
                description="AUROC, AUPRC, F1, recall, precisão e calibração.",
            ),
            PluginCapability(
                kind="evaluation",
                name="patient_level_evaluation",
                contract="patient_level_no_leakage_evaluation",
                description="Avaliação por paciente sem vazamento entre splits.",
            ),
            PluginCapability(
                kind="exporter",
                name="registry_artifact_exporter",
                contract="hash_referenced_artifacts",
                description="Exporta artefatos por URI e hash, sem payload pesado no banco.",
            ),
        )

    def validate_dataset(self, experiment: ExperimentYaml) -> list[str]:
        errors: list[str] = []
        if experiment.dataset.pairing.max_delta_hours > 24:
            errors.append("Pareamento deve respeitar janela máxima de 24 horas.")
        if not experiment.dataset.pairing.patient_level:
            errors.append("Pareamento precisa ser em nível de paciente.")
        if experiment.dataset.split.strategy != "patient":
            errors.append("Split precisa ser por paciente.")
        return errors

    def validate_task(self, experiment: ExperimentYaml) -> list[str]:
        errors: list[str] = []
        if experiment.experiment.output_mode != "structured":
            errors.append("Saída deve ser estruturada.")
        if experiment.experiment.generate_text:
            errors.append("Geração de texto deve permanecer desativada.")
        return errors

    def model_contract(self) -> dict[str, Any]:
        return {"framework": "plugin-defined", "training_implemented": False}

    def metric_names(self) -> tuple[str, ...]:
        return ("auroc", "auprc", "f1", "recall", "precision", "calibration_error")

    def evaluation_contract(self) -> dict[str, Any]:
        return {"level": "patient", "requires_no_leakage": True}

    def artifact_types(self) -> tuple[str, ...]:
        return ("checkpoint", "metrics_report", "evaluation_report")


def builtin_plugins() -> tuple[EitriPlugin, ...]:
    return (ChestXrayCt24hPlugin(),)


def discover_entrypoint_plugins(group: str = "eitri.plugins") -> list[PluginDescriptor]:
    descriptors: list[PluginDescriptor] = []
    for entrypoint in entry_points(group=group):
        plugin = entrypoint.load()
        instance = plugin() if isinstance(plugin, type) else plugin
        capabilities = instance.capabilities() if hasattr(instance, "capabilities") else ()
        descriptors.append(
            PluginDescriptor(
                name=getattr(instance, "name", entrypoint.name),
                version=getattr(instance, "version", "unknown"),
                source=f"entrypoint:{entrypoint.name}",
                description=instance.describe(),
                capabilities=tuple(capabilities),
            )
        )
    return descriptors


def discover_builtin_plugins() -> list[PluginDescriptor]:
    return [
        PluginDescriptor(
            name=plugin.name,
            version=plugin.version,
            source="builtin",
            description=plugin.describe(),
            capabilities=plugin.capabilities(),
        )
        for plugin in builtin_plugins()
    ]


def discover_filesystem_plugins(paths: list[Path] | tuple[Path, ...]) -> list[PluginDescriptor]:
    descriptors: list[PluginDescriptor] = []
    for root in paths:
        if not root.exists():
            continue
        for manifest in sorted(root.glob("*/plugin.toml")):
            descriptors.append(load_plugin_manifest(manifest))
    return descriptors


def load_plugin_manifest(path: str | Path) -> PluginDescriptor:
    manifest_path = Path(path)
    with manifest_path.open("rb") as handle:
        raw = tomllib.load(handle)
    plugin = raw.get("plugin", {})
    capabilities_raw = raw.get("capabilities", [])
    capabilities = tuple(_parse_capability(item) for item in capabilities_raw)
    return PluginDescriptor(
        name=str(plugin.get("name", manifest_path.parent.name)),
        version=str(plugin.get("version", "unknown")),
        source=str(manifest_path),
        description=str(plugin.get("description", "")),
        capabilities=capabilities,
    )


def validate_plugin_descriptor(descriptor: PluginDescriptor) -> PluginValidation:
    seen = set(descriptor.kinds)
    missing = tuple(kind for kind in REQUIRED_PLUGIN_KINDS if kind not in seen)
    errors = tuple(
        f"Capacidade sem contrato: {capability.kind}:{capability.name}"
        for capability in descriptor.capabilities
        if not capability.contract
    )
    return PluginValidation(
        plugin_name=descriptor.name,
        missing_kinds=missing,
        errors=errors,
    )


def validate_experiment_with_builtin_plugins(experiment: ExperimentYaml) -> PluginValidation:
    errors: list[str] = []
    descriptors = discover_builtin_plugins()
    for plugin in builtin_plugins():
        if isinstance(plugin, DatasetPlugin):
            errors.extend(plugin.validate_dataset(experiment))
        if isinstance(plugin, TaskPlugin):
            errors.extend(plugin.validate_task(experiment))
    aggregate = PluginDescriptor(
        name="builtin",
        version="0.1.0",
        source="builtin",
        description="Plugins internos do bootstrap.",
        capabilities=tuple(
            capability for descriptor in descriptors for capability in descriptor.capabilities
        ),
    )
    base = validate_plugin_descriptor(aggregate)
    return PluginValidation(
        plugin_name="builtin",
        missing_kinds=base.missing_kinds,
        errors=tuple([*base.errors, *errors]),
    )


def _parse_capability(raw: dict[str, Any]) -> PluginCapability:
    return PluginCapability(
        kind=raw["kind"],
        name=str(raw["name"]),
        contract=str(raw["contract"]),
        description=str(raw.get("description", "")),
    )
