"""Serviços de modelos sem acoplar a CLI ao plugin concreto."""

from __future__ import annotations

from dataclasses import dataclass

from eitri.plugins import builtin_plugins


@dataclass(frozen=True)
class ModelCatalogItem:
    name: str
    framework: str
    status: str
    plugin: str


def list_planned_models() -> list[ModelCatalogItem]:
    items: list[ModelCatalogItem] = []
    for plugin in builtin_plugins():
        if hasattr(plugin, "model_contract"):
            contract = plugin.model_contract()
            for capability in plugin.capabilities():
                if capability.kind == "model":
                    items.append(
                        ModelCatalogItem(
                            name=capability.name,
                            framework=str(contract.get("framework", "plugin-defined")),
                            status="planejado",
                            plugin=plugin.name,
                        )
                    )
    return items
