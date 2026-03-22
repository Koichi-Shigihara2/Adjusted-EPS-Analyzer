import os
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from value.stock_event_timeline.data_access import load_price_history
from value.stock_event_timeline.event_detection import detect_spikes


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

    fig = make_price_volume_figure(df, spikes)
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


def make_price_volume_figure(df: pd.DataFrame, spikes: pd.DataFrame) -> go.Figure:
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
