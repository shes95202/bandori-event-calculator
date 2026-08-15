import json
import sys

from pathlib import Path

from PySide6.QtCore import (
    QThread,
    QTimer,
    Signal,
    Qt,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from bandori_event_calculator.app import (
    BenchmarkResult,
    TierResult,
)
from bandori_event_calculator.bestdori import (
    EventSnapshot,
    Server,
    get_current_event_snapshot,
)
from bandori_event_calculator.calculator import (
    TargetCalculation,
)
from bandori_event_calculator.state import (
    AppState,
)


# =============================================================
# Application paths
# =============================================================


def get_application_directory() -> Path:
    """
    Return the directory containing the application.

    Development:
        D:/bandori-event-calculator/

    PyInstaller:
        directory containing BandoriEventCalculator.exe

    For a PyInstaller --onefile build, __file__ points to the
    temporary extraction directory, so sys.executable must be
    used instead.
    """

    if getattr(
        sys,
        "frozen",
        False,
    ):
        return Path(
            sys.executable
        ).resolve().parent

    # gui.py:
    # repository/
    # └── src/
    #     └── bandori_event_calculator/
    #         └── gui.py
    return (
        Path(__file__)
        .resolve()
        .parents[2]
    )


def get_settings_path() -> Path:
    """
    Return the shared settings.json path.

    This file is intentionally placed next to the EXE so that
    services such as Synology Drive can synchronize it across
    computers.
    """

    return (
        get_application_directory()
        / "settings.json"
    )


# =============================================================
# Bestdori background refresh
# =============================================================


class BestdoriRefreshThread(QThread):
    """
    Fetch JP and TW Bestdori data in the background.

    Both servers are fetched once per refresh operation.
    Switching servers does not trigger another fetch.
    """

    loaded = Signal(
        object,
        object,
    )

    def run(self) -> None:
        snapshots: dict[
            Server,
            EventSnapshot | None,
        ] = {}

        errors: dict[
            Server,
            str,
        ] = {}

        for server in (
            Server.JP,
            Server.TW,
        ):
            try:
                snapshots[server] = (
                    get_current_event_snapshot(
                        server
                    )
                )

            except Exception as exc:
                errors[server] = (
                    f"{type(exc).__name__}: {exc}"
                )

        self.loaded.emit(
            snapshots,
            errors,
        )


# =============================================================
# Target card
# =============================================================


class TargetCard(QGroupBox):
    """
    Display one ranking or pace target.

    Ranking targets and pace benchmarks use the same
    visual structure.
    """

    def __init__(
        self,
        title: str = "—",
    ) -> None:
        super().__init__(
            title
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        layout = QGridLayout(
            self
        )

        layout.setHorizontalSpacing(
            12
        )

        layout.setVerticalSpacing(
            6
        )

        self.current_cutoff_value = (
            self._make_value_label()
        )

        self.predicted_score_value = (
            self._make_value_label()
        )

        self.expected_score_value = (
            self._make_value_label()
        )

        self.status_value = (
            self._make_value_label()
        )

        self.remaining_score_value = (
            self._make_value_label()
        )

        self.required_games_value = (
            self._make_value_label()
        )

        self.required_boosts_value = (
            self._make_value_label()
        )

        self.required_refills_value = (
            self._make_value_label()
        )

        self.required_stars_value = (
            self._make_value_label()
        )

        self.required_hours_value = (
            self._make_value_label()
        )

        self._add_field(
            layout=layout,
            row=0,
            column=0,
            text="目前分數線",
            value=self.current_cutoff_value,
        )

        self._add_field(
            layout=layout,
            row=0,
            column=2,
            text="預測分數線",
            value=self.predicted_score_value,
        )

        self._add_field(
            layout=layout,
            row=1,
            column=0,
            text="目前應達",
            value=self.expected_score_value,
        )

        self._add_field(
            layout=layout,
            row=1,
            column=2,
            text="目前狀態",
            value=self.status_value,
        )

        self._add_field(
            layout=layout,
            row=2,
            column=0,
            text="還差分數",
            value=self.remaining_score_value,
        )

        self._add_field(
            layout=layout,
            row=2,
            column=2,
            text="還需要",
            value=self.required_games_value,
        )

        self._add_field(
            layout=layout,
            row=3,
            column=0,
            text="需要火",
            value=self.required_boosts_value,
        )

        self._add_field(
            layout=layout,
            row=3,
            column=2,
            text="回火次數",
            value=self.required_refills_value,
        )

        self._add_field(
            layout=layout,
            row=4,
            column=0,
            text="需要星石",
            value=self.required_stars_value,
        )

        self._add_field(
            layout=layout,
            row=4,
            column=2,
            text="預估時間",
            value=self.required_hours_value,
        )

        layout.setColumnStretch(
            1,
            1,
        )

        layout.setColumnStretch(
            3,
            1,
        )

    @staticmethod
    def _make_value_label() -> QLabel:
        label = QLabel(
            "—"
        )

        font = label.font()

        font.setBold(
            True
        )

        label.setFont(
            font
        )

        label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        return label

    @staticmethod
    def _add_field(
        layout: QGridLayout,
        row: int,
        column: int,
        text: str,
        value: QLabel,
    ) -> None:
        caption = QLabel(
            f"{text}："
        )

        layout.addWidget(
            caption,
            row,
            column,
        )

        layout.addWidget(
            value,
            row,
            column + 1,
        )

    def update_target(
        self,
        title: str,
        current_cutoff: int,
        predicted_score: int,
        expected_score: int,
        score_gap: int,
        calculation: TargetCalculation,
    ) -> None:
        self.setTitle(
            title
        )

        self.current_cutoff_value.setText(
            f"{current_cutoff:,}"
        )

        self.predicted_score_value.setText(
            f"{predicted_score:,}"
        )

        self.expected_score_value.setText(
            f"{expected_score:,}"
        )

        self.status_value.setText(
            self._format_score_gap(
                score_gap
            )
        )

        self.remaining_score_value.setText(
            f"{calculation.remaining_score:,}"
        )

        self.required_games_value.setText(
            f"{calculation.required_games:,} 場"
        )

        self.required_boosts_value.setText(
            f"{calculation.required_boosts:,}"
        )

        self.required_refills_value.setText(
            f"{calculation.required_refills:,}"
        )

        self.required_stars_value.setText(
            f"{calculation.required_stars:,}"
        )

        self.required_hours_value.setText(
            f"{calculation.required_hours:.1f} 小時"
        )

    def clear_target(
        self,
        title: str = "—",
    ) -> None:
        self.setTitle(
            title
        )

        labels = (
            self.current_cutoff_value,
            self.predicted_score_value,
            self.expected_score_value,
            self.status_value,
            self.remaining_score_value,
            self.required_games_value,
            self.required_boosts_value,
            self.required_refills_value,
            self.required_stars_value,
            self.required_hours_value,
        )

        for label in labels:
            label.setText(
                "—"
            )

    @staticmethod
    def _format_score_gap(
        score_gap: int,
    ) -> str:
        if score_gap > 0:
            return (
                f"落後 {score_gap:,}"
            )

        if score_gap < 0:
            return (
                f"超前 {abs(score_gap):,}"
            )

        return "剛好達標"


# =============================================================
# Main window
# =============================================================


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        # -----------------------------------------------------
        # Independent state for JP and TW
        # -----------------------------------------------------

        self.states: dict[
            Server,
            AppState,
        ] = {
            Server.JP: AppState(
                server=Server.JP,
            ),
            Server.TW: AppState(
                server=Server.TW,
            ),
        }

        self.state = self.states[
            Server.JP
        ]

        # -----------------------------------------------------
        # Shared JSON settings
        # -----------------------------------------------------

        self.settings_path = (
            get_settings_path()
        )

        self._load_settings()

        # -----------------------------------------------------
        # Bestdori state
        # -----------------------------------------------------

        self.load_errors: dict[
            Server,
            str,
        ] = {}

        self.refresh_thread: (
            BestdoriRefreshThread | None
        ) = None

        # -----------------------------------------------------
        # Window
        # -----------------------------------------------------

        self.setWindowTitle(
            "Bandori Event Calculator"
        )

        self.resize(
            1100,
            820,
        )

        self.setMinimumSize(
            900,
            700,
        )

        self._build_ui()

        self._apply_theme()

        self._connect_signals()

        self._clear_event_display()

        # Restore saved JP values into visible input fields.
        self._sync_inputs_from_state()

        # -----------------------------------------------------
        # Local recalculation timer
        # -----------------------------------------------------

        self.local_timer = QTimer(
            self
        )

        self.local_timer.timeout.connect(
            self._local_time_update
        )

        self.local_timer.start(
            60_000
        )

        # -----------------------------------------------------
        # Fetch JP + TW once when application starts
        # -----------------------------------------------------

        QTimer.singleShot(
            0,
            self.refresh_bestdori,
        )

    # =========================================================
    # JSON settings
    # =========================================================

    def _load_settings(
        self,
    ) -> None:
        """
        Load JP/TW user inputs from settings.json.

        Missing or malformed settings fall back to zero rather
        than preventing the application from starting.
        """

        if not self.settings_path.exists():
            return

        try:
            with self.settings_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(
                    file
                )

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return

        if not isinstance(
            data,
            dict,
        ):
            return

        for server in (
            Server.JP,
            Server.TW,
        ):
            server_data = data.get(
                server.name,
                {},
            )

            if not isinstance(
                server_data,
                dict,
            ):
                continue

            current_score = (
                self._safe_nonnegative_int(
                    server_data.get(
                        "current_score",
                        0,
                    )
                )
            )

            average_score = (
                self._safe_nonnegative_int(
                    server_data.get(
                        "average_score",
                        0,
                    )
                )
            )

            state = self.states[
                server
            ]

            state.current_score = (
                current_score
            )

            state.average_score = (
                average_score
            )

    def _save_settings(
        self,
    ) -> None:
        """
        Save JP/TW inputs into settings.json.

        A temporary file is written first and then replaced to
        reduce the chance of leaving a partially written JSON
        file if the application is interrupted during saving.
        """

        data = {
            server.name: {
                "current_score": (
                    state.current_score
                ),
                "average_score": (
                    state.average_score
                ),
            }
            for server, state
            in self.states.items()
        }

        temporary_path = (
            self.settings_path.with_suffix(
                ".json.tmp"
            )
        )

        try:
            self.settings_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with temporary_path.open(
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=4,
                )

                file.write(
                    "\n"
                )

            temporary_path.replace(
                self.settings_path
            )

        except OSError:
            # Saving settings should never crash the calculator.
            #
            # For example, Synology Drive may temporarily lock a
            # file while synchronizing it.
            try:
                if temporary_path.exists():
                    temporary_path.unlink()
            except OSError:
                pass

    @staticmethod
    def _safe_nonnegative_int(
        value: object,
    ) -> int:
        """
        Convert a JSON value to a non-negative integer.
        Invalid values become zero.
        """

        try:
            result = int(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0

        return max(
            result,
            0,
        )

    # =========================================================
    # Theme
    # =========================================================

    def _apply_theme(
        self,
    ) -> None:
        """
        Apply the light sky-blue theme.
        """

        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #DFF3FF;
            }

            QWidget#centralWidget {
                background-color: #DFF3FF;
            }

            QLabel {
                color: #17324D;
                background-color: transparent;
            }

            QGroupBox {
                background-color: #F8FCFF;
                color: #163A5F;

                border: 1px solid #86C8EE;
                border-radius: 8px;

                margin-top: 10px;
                padding-top: 10px;

                font-weight: 600;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;

                left: 10px;

                padding-left: 5px;
                padding-right: 5px;

                color: #1B5F8C;
                background-color: #DFF3FF;
            }

            QLineEdit {
                background-color: #FFFFFF;
                color: #17324D;

                border: 1px solid #8ACCF0;
                border-radius: 6px;

                padding: 6px 8px;

                selection-background-color: #69BDE8;
                selection-color: #FFFFFF;
            }

            QLineEdit:hover {
                border: 1px solid #55B2E6;
            }

            QLineEdit:focus {
                border: 2px solid #3CA9E3;
                padding: 5px 7px;
            }

            QComboBox {
                background-color: #FFFFFF;
                color: #17324D;

                border: 1px solid #8ACCF0;
                border-radius: 6px;

                padding: 5px 8px;
                min-width: 65px;
            }

            QComboBox:hover {
                border: 1px solid #55B2E6;
            }

            QComboBox:focus {
                border: 2px solid #3CA9E3;
            }

            QComboBox::drop-down {
                border: none;
                width: 24px;
            }

            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #17324D;

                border: 1px solid #86C8EE;

                selection-background-color: #85CEF3;
                selection-color: #12324A;
            }

            QPushButton {
                background-color: #55B7E8;
                color: #FFFFFF;

                border: 1px solid #399ED4;
                border-radius: 6px;

                padding: 6px 12px;

                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #43ACE1;
            }

            QPushButton:pressed {
                background-color: #2E96CE;
            }

            QPushButton:disabled {
                background-color: #B6D9EA;
                color: #EEF8FD;

                border: 1px solid #A2CDDF;
            }

            QToolTip {
                background-color: #FFFFFF;
                color: #17324D;

                border: 1px solid #7CC4EA;

                padding: 4px;
            }
            """
        )

    # =========================================================
    # UI
    # =========================================================

    def _build_ui(
        self,
    ) -> None:
        central_widget = QWidget()

        central_widget.setObjectName(
            "centralWidget"
        )

        self.setCentralWidget(
            central_widget
        )

        main_layout = QVBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        main_layout.setSpacing(
            10
        )

        # -----------------------------------------------------
        # Title
        # -----------------------------------------------------

        title_layout = QHBoxLayout()

        title_label = QLabel(
            "Bandori Event Calculator"
        )

        title_font = (
            title_label.font()
        )

        title_font.setPointSize(
            20
        )

        title_font.setBold(
            True
        )

        title_label.setFont(
            title_font
        )

        title_label.setStyleSheet(
            """
            color: #145B86;
            background-color: transparent;
            """
        )

        title_layout.addWidget(
            title_label
        )

        title_layout.addStretch()

        self.refresh_status_label = QLabel()

        self.refresh_status_label.setStyleSheet(
            """
            color: #277EAC;
            font-weight: 600;
            """
        )

        title_layout.addWidget(
            self.refresh_status_label
        )

        main_layout.addLayout(
            title_layout
        )

        # -----------------------------------------------------
        # Server controls
        # -----------------------------------------------------

        control_layout = QHBoxLayout()

        control_layout.addWidget(
            QLabel(
                "伺服器："
            )
        )

        self.server_combo = QComboBox()

        self.server_combo.addItem(
            "JP",
            Server.JP,
        )

        self.server_combo.addItem(
            "TW",
            Server.TW,
        )

        control_layout.addWidget(
            self.server_combo
        )

        self.refresh_button = QPushButton(
            "重新整理 Bestdori"
        )

        control_layout.addWidget(
            self.refresh_button
        )

        control_layout.addStretch()

        main_layout.addLayout(
            control_layout
        )

        # -----------------------------------------------------
        # Event information
        # -----------------------------------------------------

        event_group = QGroupBox(
            "活動資料"
        )

        event_layout = QVBoxLayout(
            event_group
        )

        self.event_name_label = QLabel(
            "尚未載入活動資料"
        )

        event_name_font = (
            self.event_name_label.font()
        )

        event_name_font.setBold(
            True
        )

        event_name_font.setPointSize(
            11
        )

        self.event_name_label.setFont(
            event_name_font
        )

        self.event_name_label.setStyleSheet(
            """
            color: #145B86;
            """
        )

        self.event_detail_label = QLabel(
            "—"
        )

        event_layout.addWidget(
            self.event_name_label
        )

        event_layout.addWidget(
            self.event_detail_label
        )

        main_layout.addWidget(
            event_group
        )

        # -----------------------------------------------------
        # Current input + event status
        # -----------------------------------------------------

        upper_layout = QHBoxLayout()

        input_group = QGroupBox(
            "目前資料"
        )

        input_layout = QGridLayout(
            input_group
        )

        self.current_score_edit = QLineEdit()

        self.current_score_edit.setPlaceholderText(
            "例如：1,260,000"
        )

        self.average_score_edit = QLineEdit()

        self.average_score_edit.setPlaceholderText(
            "例如：20,235"
        )

        input_layout.addWidget(
            QLabel(
                "目前分數："
            ),
            0,
            0,
        )

        input_layout.addWidget(
            self.current_score_edit,
            0,
            1,
        )

        input_layout.addWidget(
            QLabel(
                "一場平均分數："
            ),
            1,
            0,
        )

        input_layout.addWidget(
            self.average_score_edit,
            1,
            1,
        )

        upper_layout.addWidget(
            input_group,
            1,
        )

        status_group = QGroupBox(
            "活動狀態"
        )

        status_layout = QGridLayout(
            status_group
        )

        status_layout.addWidget(
            QLabel(
                "活動進度："
            ),
            0,
            0,
        )

        self.progress_value_label = QLabel(
            "—"
        )

        status_layout.addWidget(
            self.progress_value_label,
            0,
            1,
        )

        status_layout.addWidget(
            QLabel(
                "目前 Pace 預計最終："
            ),
            1,
            0,
        )

        self.projected_final_value_label = QLabel(
            "—"
        )

        status_layout.addWidget(
            self.projected_final_value_label,
            1,
            1,
        )

        for label in (
            self.progress_value_label,
            self.projected_final_value_label,
        ):
            font = label.font()

            font.setBold(
                True
            )

            label.setFont(
                font
            )

            label.setStyleSheet(
                """
                color: #145B86;
                """
            )

        upper_layout.addWidget(
            status_group,
            1,
        )

        main_layout.addLayout(
            upper_layout
        )

        # -----------------------------------------------------
        # Pace benchmark targets
        # -----------------------------------------------------

        benchmark_title = QLabel(
            "區間目標 — 現在需要打多少才能追上應達進度"
        )

        benchmark_font = (
            benchmark_title.font()
        )

        benchmark_font.setPointSize(
            12
        )

        benchmark_font.setBold(
            True
        )

        benchmark_title.setFont(
            benchmark_font
        )

        benchmark_title.setStyleSheet(
            """
            color: #145B86;
            """
        )

        main_layout.addWidget(
            benchmark_title
        )

        benchmark_layout = QHBoxLayout()

        self.benchmark_cards = [
            TargetCard(
                "區間目標 1"
            ),
            TargetCard(
                "區間目標 2"
            ),
        ]

        for card in (
            self.benchmark_cards
        ):
            benchmark_layout.addWidget(
                card
            )

        main_layout.addLayout(
            benchmark_layout
        )

        # -----------------------------------------------------
        # Final ranking targets
        # -----------------------------------------------------

        ranking_title = QLabel(
            "排名目標 — 活動結束前的最終需求"
        )

        ranking_font = (
            ranking_title.font()
        )

        ranking_font.setPointSize(
            12
        )

        ranking_font.setBold(
            True
        )

        ranking_title.setFont(
            ranking_font
        )

        ranking_title.setStyleSheet(
            """
            color: #145B86;
            """
        )

        main_layout.addWidget(
            ranking_title
        )

        ranking_layout = QHBoxLayout()

        self.ranking_cards = [
            TargetCard(
                "排名目標 1"
            ),
            TargetCard(
                "排名目標 2"
            ),
            TargetCard(
                "排名目標 3"
            ),
        ]

        for card in (
            self.ranking_cards
        ):
            ranking_layout.addWidget(
                card
            )

        main_layout.addLayout(
            ranking_layout
        )

        main_layout.addStretch()

    def _connect_signals(
        self,
    ) -> None:
        self.server_combo.currentIndexChanged.connect(
            self._server_changed
        )

        self.refresh_button.clicked.connect(
            self.refresh_bestdori
        )

        self.current_score_edit.textChanged.connect(
            self._current_score_changed
        )

        self.average_score_edit.textChanged.connect(
            self._average_score_changed
        )

    # =========================================================
    # Server switching
    # =========================================================

    def _server_changed(
        self,
    ) -> None:
        """
        Switch to the cached state for the selected server.

        This does NOT fetch Bestdori.
        """

        server = (
            self.server_combo.currentData()
        )

        if not isinstance(
            server,
            Server,
        ):
            return

        self.state = self.states[
            server
        ]

        self._sync_inputs_from_state()

        self._display_current_server()

    def _sync_inputs_from_state(
        self,
    ) -> None:
        """
        Restore saved values for the selected server.
        """

        self.current_score_edit.blockSignals(
            True
        )

        self.average_score_edit.blockSignals(
            True
        )

        if (
            self.state.current_score
            > 0
        ):
            self.current_score_edit.setText(
                f"{self.state.current_score:,}"
            )
        else:
            self.current_score_edit.clear()

        if (
            self.state.average_score
            > 0
        ):
            self.average_score_edit.setText(
                f"{self.state.average_score:,}"
            )
        else:
            self.average_score_edit.clear()

        self.current_score_edit.blockSignals(
            False
        )

        self.average_score_edit.blockSignals(
            False
        )

    # =========================================================
    # Bestdori refresh
    # =========================================================

    def refresh_bestdori(
        self,
    ) -> None:
        """
        Refresh JP and TW Bestdori snapshots.
        """

        if (
            self.refresh_thread
            is not None
        ):
            return

        self.refresh_button.setEnabled(
            False
        )

        self.server_combo.setEnabled(
            False
        )

        self.refresh_status_label.setText(
            "正在取得 JP / TW Bestdori 資料..."
        )

        self.refresh_thread = (
            BestdoriRefreshThread()
        )

        self.refresh_thread.loaded.connect(
            self._snapshots_loaded
        )

        self.refresh_thread.finished.connect(
            self._refresh_finished
        )

        self.refresh_thread.start()

    def _snapshots_loaded(
        self,
        snapshots: dict[
            Server,
            EventSnapshot | None,
        ],
        errors: dict[
            Server,
            str,
        ],
    ) -> None:
        self.load_errors = (
            errors
        )

        for server, state in (
            self.states.items()
        ):
            if (
                server
                not in snapshots
            ):
                continue

            state.snapshot = (
                snapshots[server]
            )

            state.recalculate()

        if errors:
            failed_servers = ", ".join(
                server.name
                for server in errors
            )

            self.refresh_status_label.setText(
                "部分資料載入失敗："
                f"{failed_servers}"
            )

        else:
            self.refresh_status_label.setText(
                "JP / TW Bestdori 資料已更新"
            )

        self._display_current_server()

    def _refresh_finished(
        self,
    ) -> None:
        if (
            self.refresh_thread
            is not None
        ):
            self.refresh_thread.deleteLater()

            self.refresh_thread = None

        self.refresh_button.setEnabled(
            True
        )

        self.server_combo.setEnabled(
            True
        )

    # =========================================================
    # Current server display
    # =========================================================

    def _display_current_server(
        self,
    ) -> None:
        snapshot = (
            self.state.snapshot
        )

        if snapshot is None:
            if (
                self.state.server
                in self.load_errors
            ):
                self.event_name_label.setText(
                    f"{self.state.server.name} "
                    "資料載入失敗"
                )

                self.event_detail_label.setText(
                    self.load_errors[
                        self.state.server
                    ]
                )

            else:
                self.event_name_label.setText(
                    f"{self.state.server.name} "
                    "目前沒有進行中的活動"
                )

                self.event_detail_label.setText(
                    "—"
                )

            self._clear_calculation_display()

            return

        event = (
            snapshot.event
        )

        self.event_name_label.setText(
            f"#{event.id} {event.name}"
        )

        self.event_detail_label.setText(
            f"{event.event_type}  |  "
            f"{event.start_datetime_local:%Y-%m-%d %H:%M}"
            " ~ "
            f"{event.end_datetime_local:%Y-%m-%d %H:%M}"
        )

        self._update_calculation_display()

    # =========================================================
    # Input
    # =========================================================

    @staticmethod
    def _parse_score(
        text: str,
    ) -> int | None:
        cleaned = (
            text.strip()
            .replace(",", "")
            .replace(" ", "")
        )

        if not cleaned:
            return 0

        if not cleaned.isdigit():
            return None

        return int(
            cleaned
        )

    def _current_score_changed(
        self,
        text: str,
    ) -> None:
        score = (
            self._parse_score(
                text
            )
        )

        if score is None:
            return

        self.state.update_current_score(
            score
        )

        # Save both JP and TW states immediately.
        self._save_settings()

        self._update_calculation_display()

    def _average_score_changed(
        self,
        text: str,
    ) -> None:
        score = (
            self._parse_score(
                text
            )
        )

        if score is None:
            return

        self.state.update_average_score(
            score
        )

        self._save_settings()

        self._update_calculation_display()

    # =========================================================
    # Local timer
    # =========================================================

    def _local_time_update(
        self,
    ) -> None:
        """
        Recalculate both cached server states locally.

        This never fetches Bestdori.
        """

        for state in (
            self.states.values()
        ):
            if (
                state.snapshot
                is None
            ):
                continue

            if (
                state.average_score
                <= 0
            ):
                continue

            state.recalculate()

        self._update_calculation_display()

    # =========================================================
    # Calculation display
    # =========================================================

    def _update_calculation_display(
        self,
    ) -> None:
        calculation = (
            self.state.calculation
        )

        if calculation is None:
            self._clear_calculation_display()

            return

        self.progress_value_label.setText(
            f"{calculation.progress:.1%}"
        )

        if (
            calculation.projected_final_score
            is not None
        ):
            self.projected_final_value_label.setText(
                f"{calculation.projected_final_score:,}"
            )
        else:
            self.projected_final_value_label.setText(
                "—"
            )

        # -----------------------------------------------------
        # Benchmark cards
        # -----------------------------------------------------

        benchmarks = list(
            calculation.benchmarks.values()
        )

        for index, card in enumerate(
            self.benchmark_cards
        ):
            if (
                index
                >= len(benchmarks)
            ):
                card.clear_target()

                card.setVisible(
                    False
                )

                continue

            benchmark = (
                benchmarks[index]
            )

            card.setVisible(
                True
            )

            self._update_benchmark_card(
                card=card,
                result=benchmark,
            )

        # -----------------------------------------------------
        # Ranking cards
        # -----------------------------------------------------

        tiers = sorted(
            calculation.tiers.items(),
            key=lambda item: item[0],
        )

        for index, card in enumerate(
            self.ranking_cards
        ):
            if (
                index
                >= len(tiers)
            ):
                card.clear_target()

                card.setVisible(
                    False
                )

                continue

            tier, tier_result = (
                tiers[index]
            )

            card.setVisible(
                True
            )

            self._update_tier_card(
                card=card,
                tier=tier,
                result=tier_result,
            )

    @staticmethod
    def _update_benchmark_card(
        card: TargetCard,
        result: BenchmarkResult,
    ) -> None:
        card.update_target(
            title=result.label,
            current_cutoff=result.current_cutoff,
            predicted_score=result.predicted_score,
            expected_score=result.expected_score,
            score_gap=result.score_gap,
            calculation=result.calculation,
        )

    @staticmethod
    def _update_tier_card(
        card: TargetCard,
        tier: int,
        result: TierResult,
    ) -> None:
        card.update_target(
            title=f"T{tier}",
            current_cutoff=result.current_cutoff,
            predicted_score=result.predicted_score,
            expected_score=result.expected_score,
            score_gap=result.score_gap,
            calculation=result.calculation,
        )

    # =========================================================
    # Clear display
    # =========================================================

    def _clear_calculation_display(
        self,
    ) -> None:
        self.progress_value_label.setText(
            "—"
        )

        self.projected_final_value_label.setText(
            "—"
        )

        for index, card in enumerate(
            self.benchmark_cards,
            start=1,
        ):
            card.clear_target(
                f"區間目標 {index}"
            )

            card.setVisible(
                True
            )

        for index, card in enumerate(
            self.ranking_cards,
            start=1,
        ):
            card.clear_target(
                f"排名目標 {index}"
            )

            card.setVisible(
                True
            )

    def _clear_event_display(
        self,
    ) -> None:
        self.event_name_label.setText(
            "尚未載入活動資料"
        )

        self.event_detail_label.setText(
            "正在準備載入 JP / TW Bestdori 資料..."
        )

        self.refresh_status_label.clear()

        self._clear_calculation_display()


# =============================================================
# Entry point
# =============================================================


def main() -> None:
    app = QApplication(
        sys.argv
    )

    window = MainWindow()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()