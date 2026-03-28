import sys
from pathlib import Path
# プロジェクトルートを sys.path に追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
# src ディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent / "src"))

import os
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from value.stock_event_timeline.data_access import load_price_history
from value.stock_event_timeline.event_detection import detect_spikes, merge_nearby_spikes
from value.stock_event_timeline.xai_client import generate_event_summary
from value.stock_event_timeline.db_manager import save_analysis, load_analysis
from value.stock_event_timeline.models import EventModel


def get_query_param(name: str, default: Optional[str] = None) -> Optional[str]:
    params = st.query_params
    val = params.get(name, [default])
    return val[0] if isinstance(val, list) else val


def main():
    st.set_page_config(page_title="Stock Event Timeline", layout="wide")

    st.title("Stock Event Timeline Dashboard")

    col1, col2 = st.columns(2)
    with col1:
        ticker = get_query_param("ticker", "TSLA")
        ticker = st.text_input("Ticker", ticker).upper()
    with col2:
        years = int(get_query_param("years", "5"))
        years = st.number_input("Period (years)", min_value=1, max_value=10, value=years)

    df = load_price_history(ticker, years)
    if df.empty:
        st.warning("No price data.")
        return

    spikes = detect_spikes(df)
    events = merge_nearby_spikes(spikes, days=3)
    # イベントを日付降順にソート
    events = events.sort_values("start_date", ascending=False)

    fig = make_price_volume_figure(df, spikes, events)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Detected spike days")
    if spikes.empty:
        st.write("No spikes detected with current thresholds.")
    else:
        st.dataframe(
            spikes[["date", "close", "return", "volume", "vol_ratio"]].assign(
                date=lambda x: x["date"].dt.strftime("%Y-%m-%d")
            )
        )

    st.subheader("Event Windows (merged spikes)")
    if events.empty:
        st.write("No events.")
    else:
        for _, event in events.iterrows():
            event_data = {
                "ticker": ticker,
                "start_date": event["start_date"].strftime("%Y-%m-%d"),
                "end_date": event["end_date"].strftime("%Y-%m-%d"),
                "spike_dates": [d.strftime("%Y-%m-%d") for d in event["spike_dates"]],
                "price_summary": {
                    "max_return": spikes.loc[spikes["date"].isin(event["spike_dates"]), "return"].max(),
                    "min_return": spikes.loc[spikes["date"].isin(event["spike_dates"]), "return"].min(),
                    "max_vol_ratio": spikes.loc[spikes["date"].isin(event["spike_dates"]), "vol_ratio"].max(),
                }
            }

            # DBから既存分析を検索
            analysis_dict = load_analysis(ticker, event["event_id"])

            if analysis_dict is None:
                # 未分析の場合はAPIを呼び出し
                with st.spinner(f"Analyzing event {event['event_id']}..."):
                    analysis_obj = generate_event_summary(event_data)
                    analysis_dict = {
                        "title": analysis_obj.title,
                        "comment": analysis_obj.comment,
                        "categories": analysis_obj.categories,
                        "causality_confidence": analysis_obj.causality_confidence
                    }
                    # DBに保存
                    save_analysis(
                        ticker,
                        event["event_id"],
                        event["start_date"].strftime("%Y-%m-%d"),
                        event["end_date"].strftime("%Y-%m-%d"),
                        analysis_dict
                    )
                analysis = analysis_obj
            else:
                # 既存データを EventModel 形式に変換（表示用）
                analysis = EventModel(
                    code=f"event_{event['event_id']}",
                    title=analysis_dict["title"],
                    comment=analysis_dict["comment"],
                    categories=analysis_dict["categories"],
                    causality_confidence=analysis_dict["causality_confidence"],
                    alternative_factors=[],
                    is_main_cause=True,
                    window_start=event["start_date"].strftime("%Y-%m-%d"),
                    window_end=event["end_date"].strftime("%Y-%m-%d")
                )

            with st.expander(f"Event {event['event_id']}: {event['start_date'].strftime('%Y-%m-%d')} to {event['end_date'].strftime('%Y-%m-%d')}"):
                st.write(f"Spike days: {', '.join([d.strftime('%Y-%m-%d') for d in event['spike_dates']])}")
                st.markdown(f"**{analysis.title}**")
                st.write(analysis.comment)
                st.caption(f"Categories: {', '.join(analysis.categories)} | Confidence: {analysis.causality_confidence}")


def make_price_volume_figure(df: pd.DataFrame, spikes: pd.DataFrame, events: pd.DataFrame = None) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Price",
            yaxis="y1",
        )
    )

    colors = ["#60a5fa"] * len(df)
    spike_dates = set(spikes["date"])
    for i, d in enumerate(df["date"]):
        if d in spike_dates:
            colors[i] = "#f97373"

    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["volume"],
            marker_color=colors,
            name="Volume",
            yaxis="y2",
            opacity=0.7,
        )
    )

    # イベントマーカーの追加
    if events is not None and not events.empty:
        marker_data = []
        for idx, event in events.iterrows():
            rep_date = event["start_date"]
            price_row = df[df["date"] == rep_date]
            if not price_row.empty:
                marker_data.append({
                    "date": rep_date,
                    "price": price_row["close"].values[0],
                    "event_id": event["event_id"]
                })
        
        if marker_data:
            marker_df = pd.DataFrame(marker_data)
            fig.add_trace(go.Scatter(
                x=marker_df["date"],
                y=marker_df["price"],
                mode="markers",
                marker=dict(size=12, color="yellow", symbol="circle", line=dict(width=1, color="black")),
                name="Event",
                text=[f"Event {eid}" for eid in marker_df["event_id"]],
                hovertemplate="Date: %{x}<br>Price: %{y:.2f}<br>%{text}<extra></extra>"
            ))

    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=40),
        xaxis=dict(domain=[0, 1]),
        yaxis=dict(title="Price", side="right"),
        yaxis2=dict(
            title="Volume",
            overlaying="y",
            side="left",
            showgrid=False,
        ),
        showlegend=True,
        template="plotly_dark",
    )
    return fig


if __name__ == "__main__":
    main()


