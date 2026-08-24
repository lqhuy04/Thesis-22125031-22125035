import unittest
from pathlib import Path
from unittest.mock import patch

from app.models.experiment_schemas import ExperimentType
from app.services.experiment_service import ExperimentService
from app.utils.reproducibility import (
    build_reproducibility_metadata,
    configuration_fingerprint,
    investment_disclaimer,
)

from tests.test_experiment_service import (
    _ConnectionStub,
    _PoolStub,
    _ResultStub,
    _detail_row,
)


class ReproducibilityTests(unittest.TestCase):
    def test_configuration_fingerprint_is_stable_and_ignores_display_name(self):
        first = {
            "experiment_name": "Lần chạy A",
            "symbol": "fpt",
            "mode": "manual",
            "data_selection": {"news": True, "fundamental": False},
        }
        same_execution = {
            "data_selection": {"fundamental": False, "news": True},
            "mode": "manual",
            "symbol": "FPT",
            "experiment_name": "Tên khác",
        }
        changed_execution = {**same_execution, "mode": "auto"}

        self.assertEqual(
            configuration_fingerprint(first),
            configuration_fingerprint(same_execution),
        )
        self.assertNotEqual(
            configuration_fingerprint(first),
            configuration_fingerprint(changed_execution),
        )

    def test_metadata_discloses_live_data_and_non_deterministic_ai(self):
        metadata = build_reproducibility_metadata(
            experiment_type="analysis",
            configuration={
                "symbol": "FPT",
                "risk_appetite": {"period": "mid_term"},
            },
            scope="single",
            symbol="FPT",
        )

        self.assertEqual(metadata["schema_version"], "1.0")
        self.assertEqual(metadata["reproducibility_level"], "configuration_only")
        self.assertFalse(metadata["data"]["immutable_snapshot"])
        self.assertFalse(metadata["ai"]["seed_supported"])
        self.assertEqual(metadata["data"]["risk_period"], "mid_term")
        self.assertRegex(metadata["data"]["as_of_date"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(len(metadata["configuration_sha256"]), 64)
        self.assertEqual(len(metadata["run_fingerprint"]), 64)

    def test_investment_disclaimer_is_defensive_copy(self):
        first = investment_disclaimer()
        first["title"] = "changed"
        second = investment_disclaimer()

        self.assertEqual(second["severity"], "warning")
        self.assertEqual(second["title"], "Không phải khuyến nghị đầu tư")
        self.assertGreaterEqual(len(second["points"]), 3)

    def test_create_persists_reproducibility_metadata(self):
        previous_table_ready = ExperimentService._table_ready
        ExperimentService._table_ready = True
        connection = _ConnectionStub([_ResultStub(row=_detail_row())])
        try:
            with patch(
                "app.services.experiment_service.get_pool",
                return_value=_PoolStub(connection),
            ):
                ExperimentService.create(
                    user_id="user-a",
                    experiment_type=ExperimentType.BACKTEST,
                    scope="single",
                    symbol="FPT",
                    mode="auto",
                    configuration={"symbol": "FPT", "mode": "auto"},
                )
        finally:
            ExperimentService._table_ready = previous_table_ready

        query, params = connection.calls[0]
        self.assertIn("configuration, reproducibility", query)
        reproducibility_jsonb = params[-1]
        self.assertIn("configuration_sha256", reproducibility_jsonb.obj)
        self.assertEqual(
            reproducibility_jsonb.obj["reproducibility_level"],
            "configuration_only",
        )

    def test_existing_experiment_table_is_migrated_idempotently(self):
        previous_table_ready = ExperimentService._table_ready
        ExperimentService._table_ready = False
        connection = _ConnectionStub([_ResultStub() for _ in range(5)])
        try:
            with patch(
                "app.services.experiment_service.get_pool",
                return_value=_PoolStub(connection),
            ):
                ExperimentService.ensure_table()
        finally:
            ExperimentService._table_ready = previous_table_ready

        statements = "\n".join(query for query, _params in connection.calls)
        self.assertIn("reproducibility JSONB", statements)
        self.assertIn("ADD COLUMN IF NOT EXISTS reproducibility", statements)
        self.assertIn("ENABLE ROW LEVEL SECURITY", statements)

    def test_warning_is_exposed_by_api_and_dashboard(self):
        backend_root = Path(__file__).parents[1]
        repository_root = backend_root.parent
        route_source = (backend_root / "app" / "routes" / "agentic.py").read_text(
            encoding="utf-8"
        )
        dashboard_html = (repository_root / "admin-dashboard" / "index.html").read_text(
            encoding="utf-8"
        )
        dashboard_js = (repository_root / "admin-dashboard" / "app.js").read_text(
            encoding="utf-8"
        )
        self.assertGreaterEqual(route_source.count('result["investment_disclaimer"]'), 2)
        self.assertIn("Không phải khuyến nghị đầu tư", dashboard_html)
        self.assertIn("Không phải khuyến nghị đầu tư", dashboard_js)

    def test_ai_comparison_prioritizes_results_and_component_scores(self):
        backend_root = Path(__file__).parents[1]
        repository_root = backend_root.parent
        route_source = (backend_root / "app" / "routes" / "agentic.py").read_text(
            encoding="utf-8"
        )
        dashboard_html = (repository_root / "admin-dashboard" / "index.html").read_text(
            encoding="utf-8"
        )
        dashboard_js = (repository_root / "admin-dashboard" / "app.js").read_text(
            encoding="utf-8"
        )
        dashboard_css = (repository_root / "admin-dashboard" / "styles.css").read_text(
            encoding="utf-8"
        )

        self.assertIn('"component_scores"', route_source)
        for score_key in ('"technical"', '"fundamental"', '"news"'):
            self.assertIn(score_key, route_source)

        for score_label in ("Điểm kỹ thuật", "Điểm cơ bản", "Điểm tin tức"):
            self.assertIn(score_label, dashboard_js)
        self.assertIn("experiments.every", dashboard_js)
        self.assertIn("sections.unshift(analysisSection)", dashboard_js)
        self.assertIn("buildComparisonSections(experiments)", dashboard_js)
        self.assertIn("len(experiment_types) != 1", route_source)
        self.assertIn("Chỉ có thể so sánh các thử nghiệm cùng loại", route_source)
        self.assertIn("selectedType !== experimentType", dashboard_js)
        self.assertIn("sections.splice(reproducibilityIndex, 1)", dashboard_js)
        self.assertIn("const allBacktest", dashboard_js)
        self.assertIn("allAnalysis || allBacktest", dashboard_js)
        self.assertIn(".comparison-card,", dashboard_css)
        self.assertIn(".agent-report-card {", dashboard_css)
        self.assertIn("padding: 20px 24px", dashboard_css)

        self.assertIn('id="experimentDetailContent"', dashboard_html)
        self.assertNotIn('id="experimentConfiguration"', dashboard_html)
        self.assertNotIn('id="experimentResultData"', dashboard_html)
        self.assertNotIn('id="experimentReproducibility"', dashboard_html)
        self.assertIn("analysisExperimentDetailHtml", dashboard_js)
        self.assertIn("Thời hạn đầu tư", dashboard_js)

    def test_backtest_uses_one_result_dashboard_for_new_and_saved_runs(self):
        backend_root = Path(__file__).parents[1]
        repository_root = backend_root.parent
        route_source = (backend_root / "app" / "routes" / "agentic.py").read_text(
            encoding="utf-8"
        )
        dashboard_html = (repository_root / "admin-dashboard" / "index.html").read_text(
            encoding="utf-8"
        )
        dashboard_js = (repository_root / "admin-dashboard" / "app.js").read_text(
            encoding="utf-8"
        )

        self.assertIn('type="button">Chạy Backtest</button>', dashboard_html)
        self.assertNotIn("Chạy Backtest & Trực quan hóa", dashboard_html)
        self.assertNotIn("Hoặc tải file JSON", dashboard_html)
        self.assertNotIn("Lịch sử Backtest (Cloud)", dashboard_html)
        self.assertNotIn('id="dragDropZone"', dashboard_html)
        self.assertNotIn('id="cloudHistoryList"', dashboard_html)
        self.assertIn("loadBacktestVisualizationForExperiment", dashboard_js)
        self.assertIn('mountBacktestVisualization("history")', dashboard_js)
        self.assertNotIn("els.tabBacktestBtn.click()", dashboard_js)
        self.assertIn('id="experimentBacktestVisualizationHost"', dashboard_html)
        self.assertGreaterEqual(dashboard_js.count("renderVisualization("), 3)
        self.assertIn('"visualization_data_url"', route_source)
        self.assertIn('"visualization_file"', route_source)


if __name__ == "__main__":
    unittest.main()
