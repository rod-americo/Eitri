"""Typer command-line interface for Eitri."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from eitri.audit import audit_bootstrap
from eitri.bootstrap import seed_initial_metastore
from eitri.config import load_config
from eitri.database import (
    DatabaseSettings,
    create_postgres_engine,
    render_postgres_ddl,
    session_factory,
)
from eitri.datasets import list_configured_datasets
from eitri.db import METASTORE_TABLES
from eitri.experiments import build_experiment_plan, list_mock_experiments
from eitri.guardrails import RunIntent, evaluate_guardrails, guardrails_pass, hash_file
from eitri.jobs import list_mock_jobs
from eitri.metrics import REQUIRED_METRICS
from eitri.mock import mock_control_plane_state
from eitri.models import list_planned_models
from eitri.observability import collect_observability_frame, persist_observability_frame
from eitri.ops import run_probe, thor_probe_commands, tyr_probe_commands
from eitri.plugins import (
    discover_builtin_plugins,
    discover_entrypoint_plugins,
    discover_filesystem_plugins,
    validate_experiment_with_builtin_plugins,
    validate_plugin_descriptor,
)
from eitri.registry import PersistentRegistry
from eitri.schemas import load_experiment_yaml
from eitri.sync import git_sync_plan, validate_destructive_sync
from eitri.telemetry import Event, JsonlEventSink
from eitri.workers import (
    WorkerJob,
    local_worker_heartbeat,
    report_to_registry,
    simulate_worker_job,
    thor_worker_contract,
)

app = typer.Typer(help="Eitri: plataforma observável para experimentos de Machine Learning.")
guardrails_app = typer.Typer(help="Avalia guardrails antes de execuções locais ou remotas.")
experiments_app = typer.Typer(help="Planeja, lista e inspeciona experimentos.")
datasets_app = typer.Typer(help="Gerencia catálogo, versões, arquivos e splits de datasets.")
models_app = typer.Typer(help="Gerencia modelos e artefatos de modelos.")
metrics_app = typer.Typer(help="Mostra métricas operacionais e de treinamento.")
hosts_app = typer.Typer(help="Mostra hosts, capacidades e papéis operacionais.")
jobs_app = typer.Typer(help="Mostra fila, jobs e progresso.")
plugins_app = typer.Typer(help="Descobre e inspeciona plugins.")
sync_app = typer.Typer(help="Planeja sincronização segura via Git, sem exclusão automática.")
metastore_app = typer.Typer(help="Inspeciona e valida o metastore PostgreSQL em Tyr.")
ops_app = typer.Typer(help="Executa probes operacionais seguros em Tyr e Thor.")
app.add_typer(guardrails_app, name="guardrails")
app.add_typer(experiments_app, name="experiments")
app.add_typer(datasets_app, name="datasets")
app.add_typer(models_app, name="models")
app.add_typer(metrics_app, name="metrics")
app.add_typer(hosts_app, name="hosts")
app.add_typer(jobs_app, name="jobs")
app.add_typer(plugins_app, name="plugins")
app.add_typer(sync_app, name="sync")
app.add_typer(metastore_app, name="metastore")
app.add_typer(ops_app, name="ops")

console = Console()
DEFAULT_CONFIG = Path("configs/eitri.example.yaml")


@app.command()
def status(config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG) -> None:
    """Mostra hosts configurados e fronteiras de armazenamento."""

    loaded = load_config(config)
    table = Table(title=f"{loaded.project_name} status")
    table.add_column("Host")
    table.add_column("Role")
    table.add_column("SSH")
    for host in loaded.hosts.values():
        table.add_row(host.name, host.role, host.ssh_alias or "-")
    console.print(table)
    console.print(f"Domain: {loaded.domain}")
    console.print(f"Dry-run default: {loaded.default_dry_run}")
    console.print(f"Telemetry log: {loaded.telemetry.event_log_path}")


@app.command()
def audit(strict: Annotated[bool, typer.Option("--strict")] = False) -> None:
    """Audita a fundação contra o objetivo do bootstrap e lista pendências."""

    report = audit_bootstrap()
    table = Table(title="Auditoria do bootstrap Eitri")
    table.add_column("Requisito")
    table.add_column("Status")
    table.add_column("Evidência")
    table.add_column("Nota")
    for item in report.requirements:
        table.add_row(
            item.key,
            item.status,
            ", ".join(item.evidence),
            item.note or "-",
        )
    console.print(table)
    console.print(f"Resumo: {report.counts}")
    if strict and not report.complete:
        raise typer.Exit(code=2)


@app.command()
def doctor(config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG) -> None:
    """Verifica dependências locais, Git, configuração, PostgreSQL e superfícies principais."""

    loaded = load_config(config)
    checks = [
        ("config", True, f"{loaded.project_name} carregado"),
        (
            "postgresql_required",
            loaded.metastore.dialect == "postgresql",
            "Metastore deve ser PostgreSQL",
        ),
        ("sqlite_forbidden", loaded.metastore.dialect != "sqlite", "SQLite não é permitido"),
        (
            "control_plane_localhost",
            loaded.control_plane.host == "127.0.0.1",
            "Bind padrão deve ser localhost",
        ),
        ("git_commit", _command_ok(["git", "rev-parse", "--verify", "HEAD"]), "HEAD deve existir"),
        ("ruff", _command_ok(["./.venv/bin/python", "-m", "ruff", "--version"]), "ruff disponível"),
        (
            "pytest",
            _command_ok(["./.venv/bin/python", "-m", "pytest", "--version"]),
            "pytest disponível",
        ),
    ]
    table = Table(title="Eitri doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detalhe")
    for name, passed, detail in checks:
        table.add_row(name, "ok" if passed else "falhou", detail)
    console.print(table)
    if not all(passed for _, passed, _ in checks):
        raise typer.Exit(code=2)


@app.command()
def validate(
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG,
    experiment: Annotated[Path | None, typer.Option("--experiment")] = None,
) -> None:
    """Valida configuração da plataforma e, opcionalmente, um YAML de experimento."""

    loaded = load_config(config)
    console.print(f"Configuração da plataforma válida: {loaded.project_name}")
    if experiment is not None:
        digest = hash_file(experiment)
        parsed = load_experiment_yaml(experiment)
        plugin_validation = validate_experiment_with_builtin_plugins(parsed)
        if not plugin_validation.passed:
            for error in plugin_validation.errors:
                console.print(f"Erro de plugin: {error}")
            if plugin_validation.missing_kinds:
                console.print(f"Capacidades ausentes: {', '.join(plugin_validation.missing_kinds)}")
            raise typer.Exit(code=2)
        console.print(
            f"Experimento válido: {parsed.experiment.name} "
            f"dataset={parsed.dataset.name}:{parsed.dataset.version} sha256={digest}"
        )


@app.command("run")
def run_experiment(
    name: Annotated[str, typer.Option("--name", help="Nome da run ou experimento.")],
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG,
    experiment: Annotated[Path | None, typer.Option("--experiment")] = None,
    dataset_hash: Annotated[str | None, typer.Option("--dataset-hash")] = None,
    target_host: Annotated[str, typer.Option("--target-host")] = "odin",
    dry_run: Annotated[bool, typer.Option("--dry-run/--execute")] = True,
    heavy: Annotated[bool, typer.Option("--heavy/--light")] = False,
) -> None:
    """Planeja uma execução; por padrão não inicia treinamento real."""

    loaded = load_config(config)
    plan = build_experiment_plan(
        name=name,
        config_path=config,
        experiment_path=experiment,
        dataset_hash=dataset_hash,
        target_host=target_host,
        dry_run=dry_run,
        heavy=heavy,
    )
    results = evaluate_guardrails(plan.intent, loaded)
    _print_guardrails(results)
    JsonlEventSink(loaded.telemetry.event_log_path).emit(
        Event(
            event_type="run.dry_planned" if dry_run else "run.requested",
            payload={
                "name": name,
                "target_host": target_host,
                "dry_run": dry_run,
                "heavy": heavy,
                "guardrails_passed": guardrails_pass(results),
                "config_hash": plan.config_hash,
            },
        )
    )
    if not guardrails_pass(results):
        raise typer.Exit(code=2)
    console.print("Run aceita para planejamento. Treinamento real ainda não é executado.")


@app.command()
def web(
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG,
    host: Annotated[str | None, typer.Option("--host")] = None,
    port: Annotated[int | None, typer.Option("--port")] = None,
) -> None:
    """Inicia o Control Plane Web em localhost por padrão."""

    loaded = load_config(config)
    bind_host = host or loaded.control_plane.host
    bind_port = port or loaded.control_plane.port
    if bind_host not in {"127.0.0.1", "localhost"} and not loaded.control_plane.allow_public_bind:
        raise typer.BadParameter(
            "O Control Plane só pode abrir fora de localhost com allow_public_bind."
        )
    import uvicorn

    uvicorn.run("eitri.web:app", host=bind_host, port=bind_port, reload=False)


@guardrails_app.command("check")
def check_guardrails(
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG,
    name: Annotated[str, typer.Option("--name")] = "dry-run",
    dataset_hash: Annotated[str | None, typer.Option("--dataset-hash")] = None,
    target_host: Annotated[str, typer.Option("--target-host")] = "odin",
    dry_run: Annotated[bool, typer.Option("--dry-run/--execute")] = True,
) -> None:
    """Avalia guardrails para uma run proposta."""

    loaded = load_config(config)
    intent = RunIntent(
        name=name,
        dataset_hash=dataset_hash,
        config_path=config,
        config_hash=hash_file(config),
        target_host=target_host,
        dry_run=dry_run,
    )
    results = evaluate_guardrails(intent, loaded)
    _print_guardrails(results)
    if not guardrails_pass(results):
        raise typer.Exit(code=2)


@experiments_app.command("plan")
def plan_experiment(
    name: Annotated[str, typer.Option("--name")],
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG,
    dataset_hash: Annotated[str | None, typer.Option("--dataset-hash")] = None,
    target_host: Annotated[str, typer.Option("--target-host")] = "odin",
    dry_run: Annotated[bool, typer.Option("--dry-run/--execute")] = True,
) -> None:
    """Planeja um experimento e persiste evento de planejamento."""

    loaded = load_config(config)
    intent = RunIntent(
        name=name,
        dataset_hash=dataset_hash,
        config_path=config,
        config_hash=hash_file(config),
        target_host=target_host,
        dry_run=dry_run,
    )
    results = evaluate_guardrails(intent, loaded)
    _print_guardrails(results)
    sink = JsonlEventSink(loaded.telemetry.event_log_path)
    sink.emit(
        Event(
            event_type="experiment.planned",
            payload={
                "name": name,
                "target_host": target_host,
                "dry_run": dry_run,
                "guardrails_passed": guardrails_pass(results),
            },
        )
    )
    if not guardrails_pass(results):
        raise typer.Exit(code=2)
    console.print("Experiment plan accepted.")


@experiments_app.command("list")
def list_experiments() -> None:
    """Lista experimentos simulados até o registry persistente estar conectado ao Tyr."""

    table = Table(title="Experimentos")
    table.add_column("Nome")
    table.add_column("Status")
    table.add_column("Progresso")
    table.add_column("Loss")
    table.add_column("Val loss")
    for item in list_mock_experiments():
        table.add_row(
            item.name,
            item.status,
            f"{item.progress}%",
            str(item.loss),
            str(item.validation_loss),
        )
    console.print(table)


@datasets_app.command("list")
def list_datasets() -> None:
    """Lista datasets configurados ou simulados para o catálogo inicial."""

    table = Table(title="Datasets")
    table.add_column("Nome")
    table.add_column("Versão")
    table.add_column("Estratégia")
    for item in list_configured_datasets():
        table.add_row(item.name, item.version, item.strategy)
    console.print(table)


@models_app.command("list")
def list_models() -> None:
    """Lista modelos registrados ou planejados."""

    table = Table(title="Modelos")
    table.add_column("Nome")
    table.add_column("Framework")
    table.add_column("Status")
    for item in list_planned_models():
        table.add_row(item.name, item.framework, item.status)
    console.print(table)


@metrics_app.command("list")
def list_metrics() -> None:
    """Lista o conjunto obrigatório de métricas observáveis."""

    table = Table(title="Métricas obrigatórias")
    table.add_column("Nome")
    for name in REQUIRED_METRICS:
        table.add_row(name)
    console.print(table)


@metrics_app.command("sample")
def sample_metrics() -> None:
    """Mostra uma amostra simulada de métricas operacionais e de treinamento."""

    table = Table(title="Amostra de métricas")
    table.add_column("Métrica")
    table.add_column("Valor")
    table.add_column("Unidade")
    for metric in mock_control_plane_state()["metrics"]:
        table.add_row(metric["name"], str(metric["value"]), str(metric["unit"] or ""))
    console.print(table)


@metrics_app.command("export-mock")
def export_mock_metrics(
    run_id: Annotated[int, typer.Option("--run-id")],
    dry_run: Annotated[bool, typer.Option("--dry-run/--execute")] = True,
    env: Annotated[str, typer.Option("--env")] = "EITRI_DATABASE_URL",
) -> None:
    """Exporta uma amostra mock de métricas, eventos e artefatos para o registry."""

    frame = collect_observability_frame()
    if dry_run:
        table = Table(title="Exportação mock de observabilidade")
        table.add_column("Tipo")
        table.add_column("Quantidade")
        table.add_row("metrics", str(len(frame.metrics)))
        table.add_row("events", str(len(frame.events)))
        table.add_row("artifacts", str(len(frame.artifacts)))
        console.print(table)
        return
    engine = create_postgres_engine(DatabaseSettings.from_env(env))
    factory = session_factory(engine)
    with factory() as session:
        registry = PersistentRegistry(session=session, owner_user="rodrigo")
        counts = persist_observability_frame(registry, run_id=run_id, frame=frame)
        session.commit()
    console.print(f"Observabilidade persistida: {counts}")


@hosts_app.command("list")
def list_hosts(config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG) -> None:
    """Lista hosts declarados e suas responsabilidades."""

    loaded = load_config(config)
    table = Table(title="Hosts")
    table.add_column("Host")
    table.add_column("Papel")
    table.add_column("SSH")
    table.add_column("Responsabilidades")
    for host in loaded.hosts.values():
        table.add_row(host.name, host.role, host.ssh_alias or "-", ", ".join(host.responsibilities))
    console.print(table)


@hosts_app.command("heartbeat")
def host_heartbeat() -> None:
    """Mostra heartbeat local no formato esperado para workers futuros."""

    heartbeat = local_worker_heartbeat()
    table = Table(title=f"Heartbeat {heartbeat.worker_name}")
    table.add_column("Campo")
    table.add_column("Valor")
    table.add_row("host", heartbeat.host_name)
    table.add_row("status", heartbeat.status)
    table.add_row("queues", ", ".join(heartbeat.queues))
    table.add_row("observed_at", heartbeat.observed_at)
    console.print(table)


@jobs_app.command("list")
def list_jobs() -> None:
    """Lista jobs simulados, fila, host e progresso."""

    table = Table(title="Jobs")
    table.add_column("ID")
    table.add_column("Host")
    table.add_column("Fila")
    table.add_column("Status")
    table.add_column("Progresso")
    for job in list_mock_jobs():
        table.add_row(job.job_id, job.host, job.queue, job.status, f"{job.progress}%")
    console.print(table)


@jobs_app.command("simulate")
def simulate_job(
    job_id: Annotated[str, typer.Option("--job-id")] = "job-dry-run-001",
    run_id: Annotated[str, typer.Option("--run-id")] = "run-dry-run-001",
    worker_name: Annotated[str, typer.Option("--worker-name")] = "odin-local",
    steps: Annotated[int, typer.Option("--steps")] = 5,
    event_log: Annotated[Path | None, typer.Option("--event-log")] = None,
    db_run_id: Annotated[int | None, typer.Option("--db-run-id")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run/--execute")] = True,
    env: Annotated[str, typer.Option("--env")] = "EITRI_DATABASE_URL",
) -> None:
    """Simula execução de worker com progresso, métricas e checkpoint."""

    sink = JsonlEventSink(event_log) if event_log else None
    report = simulate_worker_job(
        WorkerJob(
            job_id=job_id,
            run_id=run_id,
            queue="dry-run",
            target_host="odin",
            command_ref="eitri jobs simulate",
            dry_run=dry_run,
        ),
        worker_name=worker_name,
        step_count=steps,
        sink=sink,
    )
    table = Table(title=f"Worker report {report.job.job_id}")
    table.add_column("Status")
    table.add_column("Progresso")
    table.add_column("Checkpoint")
    table.add_row(report.status, f"{report.final_progress}%", report.steps[-1].checkpoint)
    console.print(table)
    if dry_run or db_run_id is None:
        return
    engine = create_postgres_engine(DatabaseSettings.from_env(env))
    factory = session_factory(engine)
    with factory() as session:
        registry = PersistentRegistry(session=session, owner_user="rodrigo")
        counts = report_to_registry(registry, report=report, db_run_id=db_run_id)
        session.commit()
    console.print(f"Relatório do worker persistido: {counts}")


@plugins_app.command("list")
def list_plugins(config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG) -> None:
    """Lista plugins disponíveis por manifesto de filesystem ou entrypoint."""

    loaded = load_config(config)
    descriptors = []
    if loaded.plugins.enabled:
        descriptors.extend(discover_builtin_plugins())
        descriptors.extend(discover_filesystem_plugins(loaded.plugins.search_paths))
        descriptors.extend(discover_entrypoint_plugins())
    table = Table(title="Eitri plugins")
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Source")
    table.add_column("Capabilities")
    table.add_column("Description")
    for descriptor in descriptors:
        table.add_row(
            descriptor.name,
            descriptor.version,
            descriptor.source,
            ", ".join(descriptor.kinds) or "-",
            descriptor.description,
        )
    console.print(table)


@plugins_app.command("validate")
def validate_plugins(config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG) -> None:
    """Valida manifestos e capacidades obrigatórias de plugins."""

    loaded = load_config(config)
    descriptors = [
        *discover_builtin_plugins(),
        *discover_filesystem_plugins(loaded.plugins.search_paths),
        *discover_entrypoint_plugins(),
    ]
    table = Table(title="Validação de plugins")
    table.add_column("Plugin")
    table.add_column("Status")
    table.add_column("Faltando")
    table.add_column("Erros")
    failed = False
    for descriptor in descriptors:
        result = validate_plugin_descriptor(descriptor)
        failed = failed or not result.passed
        table.add_row(
            result.plugin_name,
            "ok" if result.passed else "falhou",
            ", ".join(result.missing_kinds) or "-",
            "; ".join(result.errors) or "-",
        )
    console.print(table)
    if failed:
        raise typer.Exit(code=2)


@sync_app.command("plan")
def sync_plan(
    target_host: Annotated[str, typer.Option("--target-host")] = "thor",
    destructive: Annotated[bool, typer.Option("--destructive")] = False,
) -> None:
    """Planeja sincronização oficial por Git e bloqueia qualquer exclusão automática."""

    plan = git_sync_plan(target_host=target_host, destructive=destructive)
    table = Table(title="Plano de sincronização")
    table.add_column("Etapa")
    table.add_column("Comando")
    for step in plan.steps:
        table.add_row(str(step.order), step.command)
    console.print(table)
    if destructive:
        raise typer.BadParameter(
            "Sincronização destrutiva é bloqueada; liste arquivos e confirme separadamente."
        )


@sync_app.command("destructive-check")
def sync_destructive_check(
    confirmation: Annotated[str, typer.Option("--confirmation")],
    path: Annotated[list[str], typer.Option("--path")],
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG,
) -> None:
    """Valida a confirmação obrigatória antes de qualquer operação destrutiva futura."""

    loaded = load_config(config)
    result = validate_destructive_sync(confirmation, loaded, list(path))
    _print_guardrails([result])
    if not result.passed:
        raise typer.Exit(code=2)


@sync_app.command("thor-contract")
def sync_thor_contract() -> None:
    """Mostra o contrato operacional esperado para workers em Thor."""

    contract = thor_worker_contract()
    table = Table(title="Contrato Thor")
    table.add_column("Campo")
    table.add_column("Valor")
    for key, value in contract.items():
        table.add_row(key, ", ".join(value) if isinstance(value, list) else str(value))
    console.print(table)


@metastore_app.command("tables")
def metastore_tables() -> None:
    """Lista tabelas declaradas no contrato SQLAlchemy do metastore PostgreSQL."""

    table = Table(title="Tabelas do metastore")
    table.add_column("Tabela")
    for name in METASTORE_TABLES:
        table.add_row(name)
    console.print(table)


@metastore_app.command("ddl")
def metastore_ddl() -> None:
    """Renderiza DDL PostgreSQL sem abrir conexão com Tyr."""

    console.print(render_postgres_ddl())


@metastore_app.command("check-url")
def metastore_check_url(
    env: Annotated[str, typer.Option("--env")] = "EITRI_DATABASE_URL",
) -> None:
    """Valida que a URL do metastore vem do ambiente e usa PostgreSQL."""

    settings = DatabaseSettings.from_env(env)
    create_postgres_engine(settings)
    console.print(f"{env} aponta para PostgreSQL e foi aceito pelo contrato do Eitri.")


@metastore_app.command("seed-initial")
def metastore_seed_initial(
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG,
    experiment: Annotated[Path, typer.Option("--experiment")] = Path(
        "configs/experiments/chest_xray_ct_24h.yaml"
    ),
    dry_run: Annotated[bool, typer.Option("--dry-run/--execute")] = True,
    env: Annotated[str, typer.Option("--env")] = "EITRI_DATABASE_URL",
) -> None:
    """Persiste hosts e experimento inicial no metastore; por padrão só mostra o plano."""

    loaded = load_config(config)
    if dry_run:
        table = Table(title="Seed inicial do metastore")
        table.add_column("Entidade")
        table.add_column("Origem")
        table.add_row("hosts", str(config))
        table.add_row("task", "paired_imaging_structured_prediction")
        table.add_row("dataset/experiment", str(experiment))
        table.add_row("model", "structured-radiology-baseline")
        console.print(table)
        return
    engine = create_postgres_engine(DatabaseSettings.from_env(env))
    factory = session_factory(engine)
    with factory() as session:
        seed_initial_metastore(session, loaded, experiment_path=experiment)
        session.commit()
    console.print("Seed inicial persistido no metastore PostgreSQL.")


@ops_app.command("tyr-probe")
def ops_tyr_probe(
    dry_run: Annotated[bool, typer.Option("--dry-run/--execute")] = True,
) -> None:
    """Executa probes seguros em Tyr sem ler segredos nem alterar estado."""

    _run_or_print_probes(tyr_probe_commands(), dry_run=dry_run)


@ops_app.command("thor-probe")
def ops_thor_probe(
    dry_run: Annotated[bool, typer.Option("--dry-run/--execute")] = True,
) -> None:
    """Executa probes seguros em Thor para host, GPU e repositório."""

    _run_or_print_probes(thor_probe_commands(), dry_run=dry_run)


@app.command()
def tui(config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG) -> None:
    """Abre a TUI local inspirada em btop, lazygit e k9s."""

    from eitri.tui import EitriApp

    EitriApp(config_path=config).run()


def _print_guardrails(results) -> None:  # type: ignore[no-untyped-def]
    table = Table(title="Guardrails")
    table.add_column("Name")
    table.add_column("Passed")
    table.add_column("Severity")
    table.add_column("Detail")
    for result in results:
        table.add_row(result.name, "yes" if result.passed else "no", result.severity, result.detail)
    console.print(table)


def _run_or_print_probes(commands, dry_run: bool) -> None:  # type: ignore[no-untyped-def]
    table = Table(title="Probes operacionais")
    table.add_column("Probe")
    table.add_column("Status")
    table.add_column("Comando/Saída")
    for command in commands:
        if dry_run:
            table.add_row(command.name, "dry-run", " ".join(command.command))
            continue
        result = run_probe(command)
        output = result.stdout.strip() or result.stderr.strip()
        table.add_row(command.name, "ok" if result.passed else "falhou", output[:500])
    console.print(table)


def _command_ok(command: list[str]) -> bool:
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    return completed.returncode == 0
