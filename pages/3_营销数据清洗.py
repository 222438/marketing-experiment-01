"""Experiment 3 upload page, using the same CSV uploader as experiment 1."""
from pathlib import Path
import sys
import json
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1] / "experiments/experiment-3-marketing-data-cleaning"
sys.path.insert(0, str(ROOT / "scripts"))
from common import read_csv, csv_bytes
from clean_data import clean_rows

st.set_page_config(page_title="实验三 · 真实评论清洗", page_icon="🧹", layout="wide")
st.title("实验三：真实营销数据获取与清洗")
st.caption("Amazon 乐器类历史评论（截至 2014 年）。价格为元数据采集时的美元价格。")
st.info("所有评论来自公开研究数据集；未补造品牌、价格、评分、评论或日期。")
uploaded = st.file_uploader("上传实验三原始 CSV（raw_data.csv）", type=["csv"])
source = uploaded if uploaded is not None else ROOT / "data/raw/raw_data.csv"
st.caption("未上传时展示真实数据样本。上传文件只在当前会话中处理。")
try:
    raw = read_csv(source)
    clean, log = clean_rows(raw)
except (ValueError, UnicodeDecodeError, OSError) as exc:
    st.error(f"无法读取或清洗 CSV：{exc}")
    st.stop()
if not raw:
    st.warning("文件没有数据行。")
    st.stop()
a,b,c=st.columns(3)
a.metric("原始记录",len(raw))
b.metric("可用于品牌分析",len(clean))
c.metric("排除记录",len(raw)-len(clean))
st.caption("缺失品牌不猜测；原始表格保留全部行。价格以 USD 显示。")
if not clean:
    st.error("没有满足字段和数值规则的记录，请查看逐行清洗日志。")
else:
    data=pd.DataFrame(clean)
    selected=st.multiselect("品牌筛选",sorted(data.brand.unique().tolist()))
    filtered=data.loc[data.brand.isin(selected)].copy() if selected else data.copy()
    st.subheader("清洗后数据")
    st.dataframe(filtered,width="stretch",hide_index=True)
    st.download_button("下载清洗结果 CSV",csv_bytes(filtered.to_dict("records")),"clean_data.csv","text/csv")
    st.caption("完整率统计基于全部清洗记录；品牌筛选不会修改原始文件。")
    completeness=pd.DataFrame([{"字段":f,"完整率":f"{sum(bool(r[f].strip()) for r in clean)/len(clean):.1%}"} for f in data.columns])
    st.dataframe(completeness,width="stretch",hide_index=True)
with st.expander("逐行清洗日志"):
    st.dataframe(pd.DataFrame(log),width="stretch",hide_index=True)
with st.expander("原始数据（全部记录）"):
    st.dataframe(pd.DataFrame(raw),width="stretch",hide_index=True)
st.markdown("[数据来源与字段说明](https://snap.stanford.edu/data/amazon/productGraph/) · "
            "[实验三代码和记录](https://github.com/222438/marketing-experiment-01/tree/main/experiments/experiment-3-marketing-data-cleaning)")
