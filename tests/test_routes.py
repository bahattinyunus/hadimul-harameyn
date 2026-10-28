# -*- coding: utf-8 -*-
"""
tests/test_routes.py: Coğrafi menzil GeoJSON veri testleri
"""

import unittest
import json
from pathlib import Path


class TestRoutesData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_dir = Path(__file__).resolve().parent.parent
        cls.routes_dir = cls.root_dir / "data" / "routes"

    def test_caldiran_route(self):
        caldiran_file = self.routes_dir / "caldiran-expedition.geojson"
        self.assertTrue(caldiran_file.exists(), "caldiran-expedition.geojson bulunamadı!")

        with open(caldiran_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        features = data.get("features", [])
        self.assertGreaterEqual(len(features), 20, "Çaldıran seferinde en az 20 menzil olmalı")

        # İlk menzil Üsküdar, son menzil Amasya
        self.assertIn("Üsküdar", features[0]["properties"]["name"])
        self.assertIn("Amasya", features[-1]["properties"]["name"])

        # Koordinat sınırları
        for feat in features:
            coords = feat["geometry"]["coordinates"]
            lon, lat = coords[0], coords[1]
            self.assertTrue(25.0 <= lon <= 50.0, f"Boylam sınır dışı: {lon}")
            self.assertTrue(35.0 <= lat <= 45.0, f"Enlem sınır dışı: {lat}")

    def test_egypt_route(self):
        egypt_file = self.routes_dir / "egypt-conquest.geojson"
        self.assertTrue(egypt_file.exists(), "egypt-conquest.geojson bulunamadı!")

        with open(egypt_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        features = data.get("features", [])
        self.assertGreaterEqual(len(features), 18, "Mısır seferinde en az 18 menzil olmalı")

        # Sina çölü menzillerinin varlığını kontrol et
        names = [f["properties"]["name"] for f in features]
        self.assertTrue(any("Sina" in n or "Ariş" in n or "Katya" in n or "Salihiye" in n for n in names))
        self.assertTrue(any("Ridâniye" in n or "Kahire" in n for n in names))


if __name__ == "__main__":
    unittest.main()
