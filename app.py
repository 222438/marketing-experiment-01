"""Experiment 1: local CSV marketing data analysis tool.

The app intentionally performs all calculations locally. It does not call a
large-language-model API or any other external service.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st


REQUIRED_COLUMNS = ["brand", "price", "rating"]
NUMERIC_COLUMNS = ["price", "rating", "sales"]
TEXT_COLUMNS = ["brand", "product"]
SAMPLE_PATH = Path(__file__).parent / "data" / "marketing_data.csv"


def read_csv(source: BytesIO | str | Path) -> pd.DataFrame:
    """Read a UTF-8 CSV and normalize column names."""
    frame = pd.read_csv(source)
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    return frame


def missing_columns(frame: pd.DataFrame) -> list[str]:
    """Return required fields that are absent, preserving the required order."""
    return [column for column in REQUIRED_COLUMNS if column not in frame.columns]


def clean_data(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Clean whitespace and numeric values, returning the usable rows and warnings."""
    clean = frame.copy()
    warnings: list[str] = []

    for column in TEXT_COLUMNS:
        if column in clean.columns:
            clean[column] = clean[column].astype("string").str.strip()

    before = len(clean)
    for column in NUMERIC_COLUMNS:
        if column in clean.columns:
            clean[column] = pd.to_numeric(clean[column], errors="coerce")
    clean = clean.dropna(subset=REQUIRED_COLUMNS)
    clean = clean.loc[clean["brand"].ne("")].copy()
    removed = before - len(clean)
    if removed or before == 0:
        warnings.append(f"已移除 {removed} 行空值或非数字数据，统计基于剩余 {len(clean)} 行。")

    out_of_range = ((clean["rating"] < 0) | (clean["rating"] > 5)).sum()
    if out_of_range:
        warnings.append(f"发现 {out_of_range} 行评分不在 0-5 范围内，请检查原始数据。")
    return clean, warnings


def summarize_by_brand(frame: pd.DataFrame) -> pd.DataFrame:
    """Calculate the requested average price and rating for each brand."""
    aggregations = {
        "average_price": ("price", "mean"),
        "average_rating": ("rating", "mean"),
    }
    if "sales" in frame.columns:
        aggregations["total_sales"] = ("sales", "sum")
    if "product" in frame.columns:
        aggregations["product_count"] = ("product", "count")

    summary = (
        frame.groupby("brand", as_index=False)
        .agg(**aggregations)
        .sort_values("average_price", ascending=False)
    )
    summary["average_price"] = summary["average_price"].round(2)
    summary["average_rating"] = summary["average_rating"].round(2)
    if "total_sales" in summary.columns:
        summary["total_sales"] = summary["total_sales"].round(0).astype(int)
    return summary


def format_summary_columns(summary: pd.DataFrame) -> pd.DataFrame:
    """Use Chinese labels for the user-facing result table."""
    return summary.rename(
        columns={
            "brand": "品牌",
            "average_price": "平均价格",
            "average_rating": "平均评分",
            "total_sales": "总销量",
            "product_count": "商品数",
        }
    )


def load_input(uploaded_file) -> tuple[pd.DataFrame, str]:
    """Load an uploaded file or the bundled demo data."""
    if uploaded_file is not None:
        return read_csv(uploaded_file), uploaded_file.name
    return read_csv(SAMPLE_PATH), "内置演示数据 marketing_data.csv"


def main() -> None:
    st.set_page_config(
        page_title="营销数据分析工具",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("营销数据分析工具")
    st.caption("上传 CSV 后按品牌统计平均价格和平均评分。所有分析均在本地完成。")

    with st.sidebar:
        st.header("数据输入")
        uploaded_file = st.file_uploader("上传 marketing_data.csv", type=["csv"])
        st.markdown("**必需字段**")
        st.code(", ".join(REQUIRED_COLUMNS), language="text")
        st.caption("product 和 sales 可选；未上传文件时展示内置示例数据。")

    try:
        raw_data, source_name = load_input(uploaded_file)
    except (UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError, OSError) as exc:
        st.error(f"CSV 读取失败：{exc}")
        st.stop()

    missing = missing_columns(raw_data)
    if missing:
        st.error(
            "CSV 缺少必需字段："
            + ", ".join(missing)
            + "。请补齐 brand、price、rating 后重新上传。"
        )
        st.stop()

    data, warnings = clean_data(raw_data)
    if not len(data):
        st.error("没有可用于分析的数据行。请检查 brand、price、rating 是否有有效值。")
        st.stop()

    for warning in warnings:
        st.warning(warning)

    st.caption(f"数据来源：{source_name} · 可用记录：{len(data)} 行")

    summary = summarize_by_brand(data)
    brand_options = ["全部品牌", *summary["brand"].tolist()]
    selected_brand = st.selectbox("品牌筛选", brand_options)
    filtered_data = data if selected_brand == "全部品牌" else data[data["brand"] == selected_brand]
    filtered_summary = summarize_by_brand(filtered_data)

    metric_one, metric_two, metric_three, metric_four = st.columns(4)
    metric_one.metric("记录数", f"{len(filtered_data):,}")
    metric_two.metric("品牌数", f"{filtered_data['brand'].nunique():,}")
    metric_three.metric("平均价格", f"¥{filtered_data['price'].mean():,.2f}")
    metric_four.metric("平均评分", f"{filtered_data['rating'].mean():.2f} / 5")

    st.subheader("品牌分析")
    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.markdown("**各品牌平均价格**")
        st.bar_chart(filtered_summary.set_index("brand")["average_price"], y_label="价格")
    with chart_right:
        st.markdown("**各品牌平均评分**")
        st.bar_chart(filtered_summary.set_index("brand")["average_rating"], y_label="评分")

    st.subheader("统计结果")
    st.dataframe(format_summary_columns(filtered_summary), width="stretch", hide_index=True)

    with st.expander("查看原始数据"):
        st.dataframe(raw_data, width="stretch", hide_index=True)

    download_data = filtered_data.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "下载当前结果 CSV",
        data=download_data,
        file_name="marketing_analysis_filtered.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
