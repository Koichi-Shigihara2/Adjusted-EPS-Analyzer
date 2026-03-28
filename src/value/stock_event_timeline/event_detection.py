import pandas as pd


def detect_spikes(df: pd.DataFrame,
                  ret_threshold: float = 0.07,
                  vol_ratio_threshold: float = 2.0) -> pd.DataFrame:
    df = df.copy()
    df["return"] = df["close"].pct_change()
    df["vol_ma20"] = df["volume"].rolling(20).mean()
    df["vol_ratio"] = df["volume"] / df["vol_ma20"]
    cond = (df["return"].abs() >= ret_threshold) | (df["vol_ratio"] >= vol_ratio_threshold)
    spikes = df[cond].dropna(subset=["return", "vol_ratio"])
    return spikes
def merge_nearby_spikes(spikes: pd.DataFrame, days: int = 3) -> pd.DataFrame:
    """
    近接するスパイク日を統合し、イベントウィンドウとしてグループ化する。
    days: この日数以内のスパイクは同じイベントとみなす。
    戻り値: DataFrame (event_id, start_date, end_date, spike_dates)
    """
    if spikes.empty:
        return pd.DataFrame(columns=["event_id", "start_date", "end_date", "spike_dates"])

    dates = spikes["date"].sort_values().unique()
    groups = []
    current_group = [dates[0]]

    for d in dates[1:]:
        if (d - current_group[-1]).days <= days:
            current_group.append(d)
        else:
            groups.append(current_group)
            current_group = [d]
    groups.append(current_group)

    events = []
    for i, group in enumerate(groups):
        events.append({
            "event_id": i,
            "start_date": min(group),
            "end_date": max(group),
            "spike_dates": list(group)
        })
    return pd.DataFrame(events)