import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import geolib as G
import sample as S
import verify as V


CFG = {
    "slug": "demo",
    "market": "cn",
    "brand": {"name": "Acme", "aliases": [], "site": "https://acme.example.com"},
    "competitors": [],
    "questions": [{"id": "q1", "group": "推荐", "market": "cn", "text": "推荐一个工具"}],
}


def row(run_id, panel, entity_fp, *, model="m1", search=False, ok=True):
    record = {
        "run_id": run_id, "platform": "deepseek", "market": "cn", "terminal": "api",
        "sample_mode": "api", "evidence_level": "B_api_可复现", "search_enabled": search,
        "question_id": "q1", "question": "推荐一个工具", "round": 1, "ok": ok,
        "analysis": {"brand_mentioned": False, "brand_rank": 0, "candidates": [],
                     "competitors_mentioned": [], "cited_domains": [], "own_domain_cited": False},
        "measurement": {"question_panel_id": panel["id"], "question_panel_fingerprint": panel["fingerprint"],
                        "entity_catalog_fingerprint": entity_fp, "analysis_version": S.ANALYSIS_VERSION,
                        "protocol": {"provider_route": "native", "resolved_model": model}},
    }
    return record


class TestMeasurementContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.work = Path(self.tmp.name)
        self.patch = mock.patch.object(G, "WORK", self.work)
        self.patch.start()
        pdir = self.work / "demo"
        pdir.mkdir()
        G.write_json(pdir / "geo.json", CFG)

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_panel_is_frozen_and_changes_when_question_changes(self):
        cfg, first = S.ensure_active_question_panel("demo", G.load_config("demo"))
        cfg["questions"][0]["text"] = "换一种提问"
        G.save_config("demo", cfg)
        _, second = S.ensure_active_question_panel("demo", G.load_config("demo"))
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(first["questions"][0]["text"], "推荐一个工具")

    def test_segments_split_by_search_and_model(self):
        cfg, panel = S.ensure_active_question_panel("demo", G.load_config("demo"))
        entity_fp = G.fingerprint(S.entity_catalog(cfg))
        metrics = S.build_metrics("demo", "run-x", panel, cfg,
                                  [row("run-x", panel, entity_fp),
                                   row("run-x", panel, entity_fp, model="m2"),
                                   row("run-x", panel, entity_fp, search=True)], 3)
        self.assertEqual(metrics["quality"]["status"], "complete")
        self.assertEqual(len(metrics["segments"]), 3)

    def test_incomplete_or_mismatched_metric_cannot_verify(self):
        cfg, panel = S.ensure_active_question_panel("demo", G.load_config("demo"))
        entity_fp = G.fingerprint(S.entity_catalog(cfg))
        metrics = S.build_metrics("demo", "run-x", panel, cfg,
                                  [row("run-x", panel, entity_fp)], 2)
        task = {"acceptance": {"type": "auto", "check": "metrics.mention_rate_gte:cn:0.3"},
                "baseline_measurement": {"question_panel_fingerprint": panel["fingerprint"]}}
        verdict, _, _ = V.check(task, {}, metrics)
        self.assertIsNone(verdict)


if __name__ == "__main__":
    unittest.main()
