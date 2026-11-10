"""Regression tests mutate real rows only in memory, never the submitted CSV."""
import copy
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from common import read_csv, csv_bytes, FIELDS
from clean_data import clean_rows, normalize

class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=read_csv(ROOT/"data/raw/raw_data.csv")
        cls.clean=read_csv(ROOT/"data/processed/clean_data.csv")
        cls.good=cls.clean[0]

    def test_real_sample_counts_and_original_not_mutated(self):
        before=copy.deepcopy(self.raw)
        clean,logs=clean_rows(self.raw)
        self.assertEqual((len(self.raw),len(clean),len(logs)),(450,385,450))
        self.assertEqual(self.raw,before)
        self.assertEqual(clean,self.clean)

    def test_missing_column_is_clear_error(self):
        with self.assertRaisesRegex(ValueError,"brand"):
            read_csv(io.BytesIO(b"price,rating\n10,5\n"))

    def test_duplicate_headers_and_malformed_rows_rejected(self):
        payload=csv_bytes([self.good]).decode("utf-8-sig")
        with self.assertRaisesRegex(ValueError,"重复列"):
            read_csv(io.BytesIO((payload.splitlines()[0]+",brand\n").encode()))
        with self.assertRaisesRegex(ValueError,"列数"):
            read_csv(io.BytesIO((payload.splitlines()[0]+"\nwrong,row\n").encode()))

    def test_missing_brand_not_inferred_from_product(self):
        row={**self.good,"brand":""}
        clean,logs=clean_rows([row])
        self.assertFalse(clean)
        self.assertIn("brand",logs[0]["reason"])

    def test_unfamiliar_brand_retained(self):
        row={**self.good,"brand":"Unfamiliar label (unit-test mutation)"}
        clean,_=clean_rows([row])
        self.assertEqual(clean[0]["brand"],row["brand"])

    def test_invalid_numbers_dropped(self):
        for field,value in [("price","NaN"),("price","inf"),("price","-2"),("price","12.999"),
                            ("rating","6"),("rating","2.5"),("total_votes","-1")]:
            with self.subTest(field=field,value=value):
                clean,log=clean_rows([{**self.good,field:value}])
                self.assertFalse(clean)
                self.assertEqual(log[0]["action"],"drop")

    def test_inconsistent_votes_and_dates_dropped(self):
        for mutation in [{"helpful_votes":"9999","total_votes":"0"},
                         {"review_date":"2013-01-01","unix_review_time":"0"}]:
            clean,_=clean_rows([{**self.good,**mutation}])
            self.assertFalse(clean)

    def test_duplicate_id_and_duplicate_review(self):
        clean,log=clean_rows([self.good,self.good,{**self.good,"record_id":"test-other-id"}])
        self.assertEqual(len(clean),1)
        self.assertEqual([r["reason"] for r in log[1:]],["duplicate_record_id","duplicate_review"])

    def test_cleaning_idempotent_and_text_preserved(self):
        clean,logs=clean_rows(self.clean)
        self.assertEqual(clean,self.clean)
        self.assertTrue(all(r["changes"]=="[]" for r in logs))

    def test_csv_quotes_newlines_and_bom_roundtrip(self):
        row={**self.good,"review":'Quoted "review", line one\nline two'}
        self.assertEqual(read_csv(io.BytesIO(csv_bytes([row]))),[row])

    def test_schema_only_empty_csv_has_no_fake_rows(self):
        self.assertEqual(clean_rows(read_csv(io.BytesIO(csv_bytes([])))),([],[]))

class StreamlitIntegrationTests(unittest.TestCase):
    def app(self, payload=None):
        from streamlit.testing.v1 import AppTest
        path=ROOT.parents[1]/"pages/3_营销数据清洗.py"
        at=AppTest.from_file(str(path),default_timeout=30)
        if payload is None:
            return at.run()
        # AppTest does not upload files itself; patch only the uploader return value.
        with patch("streamlit.file_uploader",return_value=io.BytesIO(payload)):
            return at.run()

    def test_page_loads_real_data_and_filter_does_not_modify_original(self):
        at=self.app()
        self.assertEqual(len(at.exception),0)
        self.assertEqual([m.value for m in at.metric],["450","385","65"])
        at.multiselect[0].select("Fender").run()
        self.assertEqual(len(at.exception),0)
        self.assertTrue((at.dataframe[0].value.brand=="Fender").all())
        self.assertEqual(len(at.dataframe[-1].value),450)

    def test_upload_input_and_error_path(self):
        row=read_csv(ROOT/"data/processed/clean_data.csv")[0]
        at=self.app(csv_bytes([row]))
        self.assertEqual(len(at.exception),0)
        self.assertEqual([m.value for m in at.metric],["1","1","0"])
        at=self.app(b"price,rating\n10,5\n")
        self.assertEqual(len(at.exception),0)
        self.assertTrue(any("缺少字段" in e.value for e in at.error))

if __name__=="__main__":
    unittest.main()
