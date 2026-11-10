"""Optional UI verification; requires Playwright and a locally installed Edge browser."""
from pathlib import Path
import argparse
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--url",default="http://127.0.0.1:8513")
parser.add_argument("--channel",default="msedge")
args=parser.parse_args()
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,channel=args.channel)
    page=browser.new_page(viewport={"width":1440,"height":1050},device_scale_factor=1)
    errors=[]
    page.on("pageerror",lambda e: errors.append(str(e)))
    page.goto(args.url,wait_until="networkidle")
    page.get_by_role("link",name="营销数据清洗").click()
    page.get_by_text("实验三：真实营销数据获取与清洗",exact=True).wait_for(timeout=30000)
    page.locator("input[type=file]").set_input_files(str(ROOT/"data/raw/raw_data.csv"))
    page.get_by_role("button",name="下载清洗结果 CSV").wait_for(timeout=30000)
    with page.expect_download() as event:
        page.get_by_role("button",name="下载清洗结果 CSV").click()
    downloaded=event.value
    assert Path(downloaded.path()).read_bytes()==(ROOT/"data/processed/clean_data.csv").read_bytes()
    page.locator("input[type=file]").set_input_files({"name":"missing_fields.csv","mimeType":"text/csv","buffer":b"price,rating\n10,5\n"})
    page.get_by_text("无法读取或清洗 CSV：",exact=False).wait_for(timeout=30000)
    page.locator("input[type=file]").set_input_files(str(ROOT/"data/raw/raw_data.csv"))
    page.get_by_role("button",name="下载清洗结果 CSV").wait_for(timeout=30000)
    (ROOT/"screenshots").mkdir(exist_ok=True)
    page.screenshot(path=str(ROOT/"screenshots/experiment03.png"),full_page=True)
    report={"actual_browser_upload":True,"download_matches_clean_csv":True,"missing_fields_error":True,"page_errors":errors,"url":page.url}
    (ROOT/"reports/browser_check.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    browser.close()
    assert not errors,errors
    print("BROWSER PASS: upload, downloaded bytes, missing-column error, screenshot, no page errors")
