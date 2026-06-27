"""TUI Textual do Eitri com atualização contínua de estado simulado."""

from __future__ import annotations

from pathlib import Path

from eitri.config import load_config
from eitri.mock import mock_control_plane_state

try:
    from textual.app import App, ComposeResult
    from textual.containers import Grid
    from textual.widgets import DataTable, Footer, Header, Static
except ModuleNotFoundError:  # pragma: no cover - runtime dependency path
    App = object
    ComposeResult = object
    DataTable = Footer = Grid = Header = Static = None


if App is object:

    class EitriApp:  # type: ignore[no-redef]
        def __init__(self, config_path: Path) -> None:
            self.config_path = config_path

        def run(self) -> None:
            raise RuntimeError("Textual é necessário para executar a TUI do Eitri.")

else:

    class EitriApp(App):  # type: ignore[misc,no-redef]
        """TUI local inspirada em btop, lazygit e k9s."""

        CSS = """
        Screen { layout: vertical; }
        #summary { height: 4; padding: 1 2; background: #14181c; }
        Grid { grid-size: 2 2; grid-gutter: 1; padding: 1; }
        DataTable { height: 1fr; border: solid #2b333b; }
        """
        BINDINGS = [("q", "quit", "Sair"), ("r", "refresh", "Atualizar")]

        def __init__(self, config_path: Path) -> None:
            super().__init__()
            self.config_path = config_path
            self.config = load_config(config_path)
            self.hosts_table: DataTable | None = None
            self.jobs_table: DataTable | None = None
            self.metrics_table: DataTable | None = None
            self.events_table: DataTable | None = None

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static(
                f"{self.config.project_name} | domínio={self.config.domain} | "
                f"dry_run={self.config.default_dry_run} | polling=2s",
                id="summary",
            )
            with Grid():
                self.hosts_table = DataTable(id="hosts")
                self.hosts_table.add_columns("Host", "Papel", "Status", "Uso")
                yield self.hosts_table
                self.jobs_table = DataTable(id="jobs")
                self.jobs_table.add_columns("Job", "Host", "Fila", "Status", "Progresso")
                yield self.jobs_table
                self.metrics_table = DataTable(id="metrics")
                self.metrics_table.add_columns("Métrica", "Valor", "Unidade")
                yield self.metrics_table
                self.events_table = DataTable(id="events")
                self.events_table.add_columns("Nível", "Mensagem", "Fonte")
                yield self.events_table
            yield Footer()

        def on_mount(self) -> None:
            self.refresh_tables()
            self.set_interval(2.0, self.refresh_tables)

        def action_refresh(self) -> None:
            self.refresh_tables()

        def refresh_tables(self) -> None:
            state = mock_control_plane_state()
            self._replace_rows(
                self.hosts_table,
                [
                    (
                        item["name"],
                        item["role"],
                        item["status"],
                        f"{item.get('gpu', item.get('cpu', '-'))}%",
                    )
                    for item in state["hosts"]
                ],
            )
            self._replace_rows(
                self.jobs_table,
                [
                    (
                        item["id"],
                        item["host"],
                        item["queue"],
                        item["status"],
                        f"{item['progress']}%",
                    )
                    for item in state["jobs"]
                ],
            )
            self._replace_rows(
                self.metrics_table,
                [
                    (item["name"], str(item["value"]), str(item["unit"] or ""))
                    for item in state["metrics"]
                ],
            )
            events = state["events"] + [
                {"level": item["severity"], "message": item["message"], "source": "alerts"}
                for item in state["alerts"]
            ]
            self._replace_rows(
                self.events_table,
                [(item["level"], item["message"], item["source"]) for item in events],
            )

        @staticmethod
        def _replace_rows(table: DataTable | None, rows: list[tuple[object, ...]]) -> None:
            if table is None:
                return
            table.clear()
            for row in rows:
                table.add_row(*[str(value) for value in row])
