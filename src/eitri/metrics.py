"""Métricas operacionais e de treinamento disponíveis em todas as superfícies."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from time import time

import psutil

REQUIRED_METRICS = (
    "cpu_percent",
    "ram_percent",
    "gpu_percent",
    "vram_percent",
    "disk_percent",
    "network_rx_mbps",
    "network_tx_mbps",
    "iops_read",
    "iops_write",
    "disk_read_mbps",
    "disk_write_mbps",
    "temperature_c",
    "throughput_items_per_second",
    "eta_seconds",
    "speed_batches_per_second",
    "epoch",
    "step",
    "learning_rate",
    "loss",
    "validation_loss",
    "batch_seconds",
    "epoch_seconds",
    "remaining_seconds",
    "current_checkpoint",
    "best_checkpoint",
)


@dataclass(frozen=True)
class MetricSample:
    name: str
    value: float | int | str
    unit: str | None = None


def collect_system_metrics() -> list[MetricSample]:
    disk = psutil.disk_usage(".")
    net = psutil.net_io_counters()
    io = psutil.disk_io_counters()
    return [
        MetricSample("cpu_percent", psutil.cpu_percent(interval=None), "%"),
        MetricSample("ram_percent", psutil.virtual_memory().percent, "%"),
        MetricSample("disk_percent", disk.percent, "%"),
        MetricSample("network_rx_mbps", round(net.bytes_recv / 1024 / 1024, 2), "MB"),
        MetricSample("network_tx_mbps", round(net.bytes_sent / 1024 / 1024, 2), "MB"),
        MetricSample("iops_read", io.read_count if io else 0, "ops"),
        MetricSample("iops_write", io.write_count if io else 0, "ops"),
        MetricSample("disk_read_mbps", round((io.read_bytes if io else 0) / 1024 / 1024, 2), "MB"),
        MetricSample(
            "disk_write_mbps",
            round((io.write_bytes if io else 0) / 1024 / 1024, 2),
            "MB",
        ),
        MetricSample("temperature_c", "unavailable", "C"),
        MetricSample("gpu_percent", "unavailable", "%"),
        MetricSample("vram_percent", "unavailable", "%"),
    ]


def simulated_training_metrics(seed: int | None = None) -> list[MetricSample]:
    rng = Random(seed if seed is not None else int(time()) // 2)
    progress = rng.random()
    epoch = 1 + int(progress * 20)
    step = 1 + int(progress * 5000)
    loss = max(0.08, 1.8 * (1 - progress) + rng.random() * 0.05)
    val_loss = loss + rng.random() * 0.12
    return [
        MetricSample("throughput_items_per_second", round(80 + progress * 45, 2), "items/s"),
        MetricSample("eta_seconds", int((1 - progress) * 7200), "s"),
        MetricSample("speed_batches_per_second", round(2.5 + progress, 2), "batch/s"),
        MetricSample("epoch", epoch),
        MetricSample("step", step),
        MetricSample("learning_rate", round(0.0003 * (1 - progress), 8)),
        MetricSample("loss", round(loss, 4)),
        MetricSample("validation_loss", round(val_loss, 4)),
        MetricSample("batch_seconds", round(0.35 + rng.random() * 0.08, 3), "s"),
        MetricSample("epoch_seconds", int(220 + rng.random() * 40), "s"),
        MetricSample("remaining_seconds", int((1 - progress) * 7200), "s"),
        MetricSample("current_checkpoint", f"epoch-{epoch:03d}.ckpt"),
        MetricSample("best_checkpoint", f"epoch-{max(1, epoch - 2):03d}.ckpt"),
        MetricSample("gpu_percent", round(65 + rng.random() * 25, 1), "%"),
        MetricSample("vram_percent", round(52 + rng.random() * 28, 1), "%"),
        MetricSample("temperature_c", round(61 + rng.random() * 9, 1), "C"),
    ]
