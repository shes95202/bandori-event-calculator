import json
import math
import sys
import time

from pathlib import Path

from PySide6.QtCore import (
    QThread,
    QTimer,
    Signal,
    Qt,
)
from PySide6.QtGui import (
    QIcon,
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
    Cutoff,
    EventSnapshot,
    Server,
    get_display_event_snapshot,
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

    For a PyInstaller --onefile build, sys.executable is used
    for persistent files such as settings.json.
    """

    if getattr(
        sys,
        "frozen",
        False,
    ):
        return (
            Path(sys.executable)
            .resolve()
            .parent
        )

    return (
        Path(__file__)
        .resolve()
        .parents[2]
    )


def get_resource_path(
    relative_path: str,
) -> Path:
    """
    Return a path to a bundled application resource.

    Development:
        repository/assets/icon.ico

    PyInstaller --onefile:
        temporary extraction directory/assets/icon.ico
    """

    if getattr(
        sys,
        "frozen",
        False,
    ):
        bundle_dir = Path(
            getattr(
                sys,
                "_MEIPASS",
                Path(sys.executable).parent,
            )
        )

        return (
            bundle_dir
            / relative_path
        )

    return (
        get_application_directory()
        / relative_path
    )


def get_settings_path() -> Path:
    """
    Return the shared settings.json path.

    The file is intentionally stored next to the EXE so that
    Synology Drive can synchronize it between computers.
    """

    return (
        get_application_directory()
        / "settings.json"
    )


def get_icon_path() -> Path:
    """Return the application icon path."""

    return get_resource_path(
        "assets/icon.ico"
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
                    get_display_event_snapshot(
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
# Historical final-cutoff card
# =============================================================


class FinalCutoffCard(QGroupBox):
    """Display the final/latest cutoff of a completed event tier."""

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

        self.cutoff_value = QLabel(
            "—"
        )

        self.updated_value = QLabel(
            "—"
        )

        for label in (
            self.cutoff_value,
            self.updated_value,
        ):
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

        layout.addWidget(
            QLabel(
                "最終分數線："
            ),
            0,
            0,
        )

        layout.addWidget(
            self.cutoff_value,
            0,
            1,
        )

        layout.addWidget(
            QLabel(
                "最後更新："
            ),
            1,
            0,
        )

        layout.addWidget(
            self.updated_value,
            1,
            1,
        )

        layout.setColumnStretch(
            1,
            1,
        )

    def update_cutoff(
        self,
        tier: int,
        cutoff: Cutoff,
    ) -> None:
        self.setTitle(
            f"T{tier}"
        )

        self.cutoff_value.setText(
            f"{cutoff.score:,}"
        )

        self.updated_value.setText(
            f"{cutoff.datetime_local:%Y-%m-%d %H:%M}"
        )

    def clear_cutoff(
        self,
        title: str = "—",
    ) -> None:
        self.setTitle(
            title
        )
        self.cutoff_value.setText(
            "—"
        )
        self.updated_value.setText(
            "—"
        )


# =============================================================
# Target card
# =============================================================


class TargetCard(QGroupBox):
    """
    Display one ranking or pace target.

    Ranking targets use the normal resource requirement view.

    Pace benchmarks switch to a buffer-oriented view when the
    player is already ahead of the expected event pace.
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

        # -----------------------------------------------------
        # Values
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Fixed fields
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Dynamic fields
        #
        # These labels change when a benchmark target is ahead.
        # -----------------------------------------------------

        self.remaining_score_caption = (
            self._add_field(
                layout=layout,
                row=2,
                column=0,
                text="還差分數",
                value=self.remaining_score_value,
            )
        )

        self.required_games_caption = (
            self._add_field(
                layout=layout,
                row=2,
                column=2,
                text="還需要",
                value=self.required_games_value,
            )
        )

        self.required_boosts_caption = (
            self._add_field(
                layout=layout,
                row=3,
                column=0,
                text="需要火",
                value=self.required_boosts_value,
            )
        )

        self.required_refills_caption = (
            self._add_field(
                layout=layout,
                row=3,
                column=2,
                text="回火次數",
                value=self.required_refills_value,
            )
        )

        self.required_stars_caption = (
            self._add_field(
                layout=layout,
                row=4,
                column=0,
                text="需要星石",
                value=self.required_stars_value,
            )
        )

        self.required_hours_caption = (
            self._add_field(
                layout=layout,
                row=4,
                column=2,
                text="預估時間",
                value=self.required_hours_value,
            )
        )

        layout.setColumnStretch(
            1,
            1,
        )

        layout.setColumnStretch(
            3,
            1,
        )

    # =========================================================
    # Field helpers
    # =========================================================

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
    ) -> QLabel:
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

        return caption

    def _set_default_requirement_labels(
        self,
    ) -> None:
        """Restore the normal resource requirement labels."""

        self.remaining_score_caption.setText(
            "還差分數："
        )

        self.required_games_caption.setText(
            "還需要："
        )

        self.required_boosts_caption.setText(
            "需要火："
        )

        self.required_refills_caption.setText(
            "回火次數："
        )

        self.required_stars_caption.setText(
            "需要星石："
        )

        self.required_hours_caption.setText(
            "預估時間："
        )

    def _set_ahead_buffer_labels(
        self,
    ) -> None:
        """Use buffer-oriented labels for an ahead pace target."""

        self.remaining_score_caption.setText(
            "超前分數："
        )

        self.required_games_caption.setText(
            "完整場緩衝："
        )

        self.required_boosts_caption.setText(
            "火力緩衝："
        )

        self.required_refills_caption.setText(
            "回火需求："
        )

        self.required_stars_caption.setText(
            "星石需求："
        )

        self.required_hours_caption.setText(
            "時間緩衝："
        )

    @staticmethod
    def _format_buffer_time(
        minutes: float,
    ) -> str:
        """
        Format an ahead-time buffer.

        Small buffers are easier to understand in minutes,
        while large buffers are shown in hours.
        """

        if minutes < 60:
            return (
                f"{minutes:.1f} 分鐘"
            )

        return (
            f"{minutes / 60:.1f} 小時"
        )

    @staticmethod
    def _format_pace_buffer(
        pace_buffer_games: float,
    ) -> str:
        """Format a signed Pace Buffer value."""

        if abs(
            pace_buffer_games
        ) < 0.005:
            return "0.00"

        return (
            f"{pace_buffer_games:+.2f}"
        )

    # =========================================================
    # Normal ranking target
    # =========================================================

    def update_target(
        self,
        title: str,
        current_cutoff: int,
        predicted_score: int,
        expected_score: int,
        score_gap: int,
        calculation: TargetCalculation,
    ) -> None:
        """
        Update a normal ranking target.

        Ranking targets intentionally retain the original
        requirement-oriented display.
        """

        self._set_default_requirement_labels()

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

    # =========================================================
    # Pace / benchmark target
    # =========================================================

    def update_benchmark_target(
        self,
        title: str,
        current_cutoff: int,
        predicted_score: int,
        expected_score: int,
        score_gap: int,
        calculation: TargetCalculation,
        average_score: int,
    ) -> None:
        """
        Update a pace benchmark.

        Pace Buffer is:

            (current_score - expected_score) / average_score

        Since score_gap is:

            expected_score - current_score

        this is equivalent to:

            -score_gap / average_score

        Positive = ahead.
        Negative = behind.
        """

        if average_score > 0:
            pace_buffer_games = (
                -score_gap
                / average_score
            )
        else:
            pace_buffer_games = 0.0

        pace_buffer_text = (
            self._format_pace_buffer(
                pace_buffer_games
            )
        )

        self.setTitle(
            f"{title}  |  "
            f"Pace Buffer {pace_buffer_text} 場"
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

        # -----------------------------------------------------
        # Behind or exactly on pace
        #
        # Keep the original resource requirement display.
        # -----------------------------------------------------

        if score_gap >= 0:
            self._set_default_requirement_labels()

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

            return

        # -----------------------------------------------------
        # Ahead of pace
        #
        # Instead of a row of zero requirements, show how much
        # buffer the player currently has.
        # -----------------------------------------------------

        self._set_ahead_buffer_labels()

        ahead_score = abs(
            score_gap
        )

        full_game_buffer = int(
            pace_buffer_games
        )

        boost_buffer = (
            pace_buffer_games
            * 3
        )

        time_buffer_minutes = (
            pace_buffer_games
            * 3
        )

        self.remaining_score_value.setText(
            f"{ahead_score:,}"
        )

        self.required_games_value.setText(
            f"{full_game_buffer:,} 場"
        )

        self.required_boosts_value.setText(
            f"{boost_buffer:.1f} 火"
        )

        # Negative refill/star requirements do not have a useful
        # real-world meaning, so show that no refill is required.
        self.required_refills_value.setText(
            "不需要"
        )

        self.required_stars_value.setText(
            "不需要"
        )

        self.required_hours_value.setText(
            self._format_buffer_time(
                time_buffer_minutes
            )
        )

    # =========================================================
    # Clear
    # =========================================================

    def clear_target(
        self,
        title: str = "—",
    ) -> None:
        self._set_default_requirement_labels()

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

        icon_path = (
            get_icon_path()
        )

        if icon_path.exists():
            self.setWindowIcon(
                QIcon(
                    str(icon_path)
                )
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
        # Live event countdown timer
        #
        # Only the countdown label is updated every second.
        # The heavier pace calculations continue to refresh
        # once per minute via local_timer above.
        # -----------------------------------------------------

        self.countdown_timer = QTimer(
            self
        )

        self.countdown_timer.timeout.connect(
            self._update_countdown_display
        )

        self.countdown_timer.start(
            1_000
        )

        # -----------------------------------------------------
        # Fetch JP + TW once at application startup
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
        """Load JP/TW player inputs from settings.json."""

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
        """Save JP/TW inputs into settings.json."""

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
            try:
                if temporary_path.exists():
                    temporary_path.unlink()

            except OSError:
                pass

    @staticmethod
    def _safe_nonnegative_int(
        value: object,
    ) -> int:
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
        """Apply the light sky-blue theme."""

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
        # Current data + event status
        # -----------------------------------------------------

        upper_layout = QHBoxLayout()

        input_group = QGroupBox(
            "目前資料"
        )

        input_layout = QGridLayout(
            input_group
        )

        self.current_score_edit = (
            QLineEdit()
        )

        self.current_score_edit.setPlaceholderText(
            "例如：1,260,000"
        )

        self.average_score_edit = (
            QLineEdit()
        )

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

        self.progress_value_label = (
            QLabel(
                "—"
            )
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

        self.projected_final_value_label = (
            QLabel(
                "—"
            )
        )

        status_layout.addWidget(
            self.projected_final_value_label,
            1,
            1,
        )

        status_layout.addWidget(
            QLabel(
                "距離活動結束："
            ),
            2,
            0,
        )

        self.countdown_value_label = (
            QLabel(
                "—"
            )
        )

        status_layout.addWidget(
            self.countdown_value_label,
            2,
            1,
        )

        for label in (
            self.progress_value_label,
            self.projected_final_value_label,
            self.countdown_value_label,
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
        # Pace / interval targets
        # -----------------------------------------------------

        self.benchmark_title = QLabel(
            "區間目標 — 現在需要打多少才能追上應達進度"
        )

        benchmark_font = (
            self.benchmark_title.font()
        )

        benchmark_font.setPointSize(
            12
        )

        benchmark_font.setBold(
            True
        )

        self.benchmark_title.setFont(
            benchmark_font
        )

        self.benchmark_title.setStyleSheet(
            """
            color: #145B86;
            """
        )

        main_layout.addWidget(
            self.benchmark_title
        )

        benchmark_layout = (
            QHBoxLayout()
        )

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

        self.ranking_title = QLabel(
            "排名目標 — 活動結束前的最終需求"
        )

        ranking_font = (
            self.ranking_title.font()
        )

        ranking_font.setPointSize(
            12
        )

        ranking_font.setBold(
            True
        )

        self.ranking_title.setFont(
            ranking_font
        )

        self.ranking_title.setStyleSheet(
            """
            color: #145B86;
            """
        )

        main_layout.addWidget(
            self.ranking_title
        )

        ranking_layout = (
            QHBoxLayout()
        )

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

        # -----------------------------------------------------
        # Previous event final cutoffs
        # -----------------------------------------------------

        self.history_title = QLabel(
            "上一個活動 — 最終分數線"
        )

        history_font = (
            self.history_title.font()
        )

        history_font.setPointSize(
            12
        )

        history_font.setBold(
            True
        )

        self.history_title.setFont(
            history_font
        )

        self.history_title.setStyleSheet(
            """
            color: #145B86;
            """
        )

        main_layout.addWidget(
            self.history_title
        )

        history_layout = QHBoxLayout()

        self.history_cards = [
            FinalCutoffCard(
                "歷史分數線 1"
            ),
            FinalCutoffCard(
                "歷史分數線 2"
            ),
            FinalCutoffCard(
                "歷史分數線 3"
            ),
        ]

        for card in self.history_cards:
            card.setVisible(
                False
            )
            history_layout.addWidget(
                card
            )

        self.history_title.setVisible(
            False
        )

        main_layout.addLayout(
            history_layout
        )

        main_layout.addStretch()

    # =========================================================
    # Signals
    # =========================================================

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
        self.current_score_edit.blockSignals(
            True
        )

        self.average_score_edit.blockSignals(
            True
        )

        if self.state.current_score > 0:
            self.current_score_edit.setText(
                f"{self.state.current_score:,}"
            )

        else:
            self.current_score_edit.clear()

        if self.state.average_score > 0:
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
        if self.refresh_thread is not None:
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
            if server not in snapshots:
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
        if self.refresh_thread is not None:
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
            self._show_active_sections()

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
                    "目前沒有可顯示的活動資料"
                )

                self.event_detail_label.setText(
                    "—"
                )

            self._clear_calculation_display()

            return

        self._show_active_sections()

        event = (
            snapshot.event
        )

        self.event_name_label.setText(
            f"#{event.id} {event.name}"
        )

        event_detail = (
            f"{event.event_type}  |  "
            f"{event.start_datetime_local:%Y-%m-%d %H:%M}"
            " ~ "
            f"{event.end_datetime_local:%Y-%m-%d %H:%M}"
        )

        if not snapshot.is_active:
            event_detail += "  |  已結束"

        self.event_detail_label.setText(
            event_detail
        )

        self._update_calculation_display()
        self._update_countdown_display()

    def _display_previous_event(
        self,
        snapshot: EventSnapshot,
    ) -> None:
        """Display the most recently completed event as history."""

        event = snapshot.event

        self.event_name_label.setText(
            f"{self.state.server.name} 目前沒有進行中的活動"
        )

        self.event_detail_label.setText(
            f"上一個活動：#{event.id} {event.name}  |  "
            f"{event.event_type}  |  "
            f"{event.start_datetime_local:%Y-%m-%d %H:%M}"
            " ~ "
            f"{event.end_datetime_local:%Y-%m-%d %H:%M}  |  已結束"
        )

        self.progress_value_label.setText(
            "已結束"
        )

        self.projected_final_value_label.setText(
            "不適用"
        )

        self._show_history_sections(
            snapshot
        )

    def _show_active_sections(
        self,
    ) -> None:
        self.benchmark_title.setVisible(
            True
        )
        self.ranking_title.setVisible(
            True
        )

        for card in self.benchmark_cards:
            card.setVisible(
                True
            )

        for card in self.ranking_cards:
            card.setVisible(
                True
            )

        self.history_title.setVisible(
            False
        )

        for card in self.history_cards:
            card.setVisible(
                False
            )

    def _show_history_sections(
        self,
        snapshot: EventSnapshot,
    ) -> None:
        self.benchmark_title.setVisible(
            False
        )
        self.ranking_title.setVisible(
            False
        )

        for card in self.benchmark_cards:
            card.setVisible(
                False
            )

        for card in self.ranking_cards:
            card.setVisible(
                False
            )

        self.history_title.setVisible(
            True
        )

        tiers = sorted(
            snapshot.cutoffs.items(),
            key=lambda item: item[0],
        )

        for index, card in enumerate(
            self.history_cards
        ):
            if index >= len(
                tiers
            ):
                card.clear_cutoff()
                card.setVisible(
                    False
                )
                continue

            tier, cutoff = tiers[index]

            card.update_cutoff(
                tier=tier,
                cutoff=cutoff,
            )
            card.setVisible(
                True
            )

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
    # Event countdown
    # =========================================================

    def _update_countdown_display(
        self,
    ) -> None:
        """Update the remaining event time once per second."""

        snapshot = (
            self.state.snapshot
        )

        if snapshot is None:
            self.countdown_value_label.setText(
                "—"
            )
            return

        if not snapshot.is_active:
            self.countdown_value_label.setText(
                "已結束"
            )
            return

        remaining_seconds = math.ceil(
            snapshot.event.end_at_ms / 1000
            - time.time()
        )

        if remaining_seconds <= 0:
            self.countdown_value_label.setText(
                "已結束"
            )
            return

        days, remainder = divmod(
            remaining_seconds,
            86_400,
        )

        hours, remainder = divmod(
            remainder,
            3_600,
        )

        minutes, seconds = divmod(
            remainder,
            60,
        )

        self.countdown_value_label.setText(
            f"{days} 天 {hours} 小時 "
            f"{minutes} 分 {seconds} 秒"
        )

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
            if state.snapshot is None:
                continue

            if state.average_score <= 0:
                continue

            state.recalculate()

        self._update_calculation_display()
        self._update_countdown_display()

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
        # Benchmark / pace cards
        # -----------------------------------------------------

        benchmarks = list(
            calculation.benchmarks.values()
        )

        for index, card in enumerate(
            self.benchmark_cards
        ):
            if index >= len(
                benchmarks
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
                average_score=calculation.average_score,
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
            if index >= len(
                tiers
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
        average_score: int,
    ) -> None:
        card.update_benchmark_target(
            title=result.label,
            current_cutoff=result.current_cutoff,
            predicted_score=result.predicted_score,
            expected_score=result.expected_score,
            score_gap=result.score_gap,
            calculation=result.calculation,
            average_score=average_score,
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

        self.countdown_value_label.setText(
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

    app.setApplicationName(
        "Bandori Event Calculator"
    )

    icon_path = (
        get_icon_path()
    )

    if icon_path.exists():
        app.setWindowIcon(
            QIcon(
                str(icon_path)
            )
        )

    window = MainWindow()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()