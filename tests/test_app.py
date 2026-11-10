import unittest
from pathlib import Path

import pandas as pd

from app import clean_data, missing_columns, read_csv, summarize_by_brand


ROOT = Path(__file__).parents[1]


class MarketingAnalysisTests(unittest.TestCase):
    def test_normal_csv_has_expected_brand_summary(self):
        frame = read_csv(ROOT / "data" / "test_normal.csv")
        clean, warnings = clean_data(frame)
        summary = summarize_by_brand(clean)

        self.assertFalse(warnings)
        self.assertEqual(len(clean), 4)
        self.assertEqual(summary.loc[summary["brand"] == "星河", "average_price"].iloc[0], 2699.0)

    def test_missing_fields_are_reported(self):
        frame = read_csv(ROOT / "data" / "test_missing_fields.csv")
        self.assertEqual(missing_columns(frame), ["rating"])

    def test_empty_rows_produce_no_usable_data(self):
        frame = read_csv(ROOT / "data" / "test_empty.csv")
        clean, warnings = clean_data(frame)
        self.assertTrue(clean.empty)
        self.assertTrue(any("移除" in warning for warning in warnings))

    def test_invalid_numeric_value_is_removed(self):
        frame = pd.DataFrame(
            {
                "brand": ["星河", "青禾"],
                "product": ["耳机", "手表"],
                "price": [399, "unknown"],
                "rating": [4.5, 4.2],
                "sales": [10, 20],
            }
        )
        clean, warnings = clean_data(frame)
        self.assertEqual(len(clean), 1)
        self.assertTrue(warnings)

    def test_empty_required_values_are_reported_and_excluded(self):
        frame = read_csv(ROOT / "data" / "test_empty_values.csv")
        original = frame.copy(deep=True)
        clean, warnings = clean_data(frame)

        self.assertEqual(len(clean), 2)
        self.assertTrue(any("3 行" in warning for warning in warnings))
        pd.testing.assert_frame_equal(frame, original)

    def test_product_and_sales_are_optional(self):
        frame = pd.DataFrame({"brand": ["星河"], "price": [100], "rating": [4.5]})

        clean, warnings = clean_data(frame)
        summary = summarize_by_brand(clean)

        self.assertFalse(warnings)
        self.assertEqual(summary.loc[0, "average_price"], 100.0)
        self.assertEqual(summary.loc[0, "average_rating"], 4.5)
        self.assertNotIn("total_sales", summary.columns)


if __name__ == "__main__":
    unittest.main()
