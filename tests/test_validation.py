# -*- coding: utf-8 -*-
"""
tests/test_validation.py: Veri doğrulama motoru birim testleri
"""

import unittest
from pathlib import Path
from tools.validate_data import DataValidator


class TestDataValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_dir = Path(__file__).resolve().parent.parent
        cls.validator = DataValidator(root_dir=cls.root_dir, verbose=False)
        cls.validator.load_schemas()

    def test_schemas_loaded(self):
        """Tüm temel JSON şemalarının başarıyla yüklendiğini doğrular."""
        expected_schemas = {
            "campaign.schema.json",
            "route-node.schema.json",
            "timeline.schema.json",
            "primary-sources.schema.json",
            "quotes.schema.json"
        }
        loaded = set(self.validator.schemas.keys())
        self.assertTrue(expected_schemas.issubset(loaded), f"Eksik şemalar: {expected_schemas - loaded}")

    def test_full_validation_passes(self):
        """Depodaki tüm verilerin sıfır hata ile doğrulandığını teyit eder."""
        success = self.validator.run_all()
        self.assertTrue(success, f"Doğrulama başarısız oldu. Hatalar: {self.validator.errors}")
        self.assertEqual(len(self.validator.errors), 0)


if __name__ == "__main__":
    unittest.main()
