# -*- coding: utf-8 -*-
"""
tests/test_maps.py: Harita üretim motoru birim testleri
"""

import unittest
from pathlib import Path
from tools.generate_route_map import RouteMapGenerator


class TestRouteMapGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_dir = Path(__file__).resolve().parent.parent
        cls.output_dir = cls.root_dir / "build"
        cls.generator = RouteMapGenerator(root_dir=cls.root_dir, output_dir=cls.output_dir)

    def test_generate_caldiran_html(self):
        out = self.generator.generate_interactive_html("caldiran")
        self.assertTrue(out.exists())
        content = out.read_text(encoding="utf-8")
        self.assertIn("Çaldıran Seferi", content)
        self.assertIn("leaflet.js", content)
        self.assertIn("MNZ-001", content)

    def test_generate_egypt_html(self):
        out = self.generator.generate_interactive_html("egypt")
        self.assertTrue(out.exists())
        content = out.read_text(encoding="utf-8")
        self.assertIn("Mısır", content)
        self.assertIn("leaflet.js", content)
        self.assertIn("Ridâniye", content)

    def test_portal_index(self):
        self.generator.generate_portal_index()
        index_file = self.output_dir / "index.html"
        self.assertTrue(index_file.exists())
        content = index_file.read_text(encoding="utf-8")
        self.assertIn("hadimul-harameyn", content)
        self.assertIn("caldiran-campaign-map.html", content)
        self.assertIn("egypt-campaign-map.html", content)


if __name__ == "__main__":
    unittest.main()
