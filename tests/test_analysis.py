# -*- coding: utf-8 -*-
"""
tests/test_analysis.py: Analitik hesaplama ve arama motoru birim testleri
"""

import unittest
from pathlib import Path
from tools.analyze_campaigns import CampaignAnalyzer, haversine
from tools.search_corpus import CorpusSearchEngine


class TestCampaignAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_dir = Path(__file__).resolve().parent.parent
        cls.analyzer = CampaignAnalyzer(root_dir=cls.root_dir)
        cls.searcher = CorpusSearchEngine(root_dir=cls.root_dir)

    def test_haversine_distance(self):
        # İstanbul (28.9784, 41.0082) ile Ankara (32.8597, 39.9334) arası ~350 km
        dist = haversine([28.9784, 41.0082], [32.8597, 39.9334])
        self.assertGreater(dist, 340)
        self.assertLess(dist, 360)

    def test_all_campaigns_metrics(self):
        metrics = self.analyzer.get_summary_metrics()
        self.assertEqual(metrics["total_campaign_routes"], 4)
        self.assertEqual(metrics["total_georeferenced_menzils"], 60)
        self.assertEqual(metrics["registered_campaigns"], 6)
        self.assertEqual(metrics["verified_primary_quotes"], 50)
        self.assertEqual(metrics["primary_source_works"], 18)
        self.assertGreater(metrics["total_linear_distance_km"], 5000)

    def test_search_engine_quotes(self):
        results = self.searcher.search_quotes("Sinan Paşa")
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(any("QTE-003" == q.get("quote_id") for q in results))

    def test_search_engine_routes(self):
        results = self.searcher.search_routes("El-Ariş")
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(any("MNZ-034" in r["node"]["node_id"] for r in results))

    def test_search_engine_all(self):
        results = self.searcher.run_search("Çaldıran", "all")
        self.assertIn("quotes", results)
        self.assertIn("campaigns", results)
        self.assertIn("routes", results)
        self.assertIn("timeline", results)
        self.assertGreater(len(results["campaigns"]), 0)


if __name__ == "__main__":
    unittest.main()
