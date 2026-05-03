"""
Saxo OpenAPI で5分足データの取得可能期間を確認する
saxo_token.txt にトークンを保存してから実行してください。
"""

import sys
import requests
import pandas as pd

try:
    with open("saxo_token.txt", encoding="utf-8") as f:
        TOKEN = f.read().strip()
    TOKEN = ''.join(c for c in TOKEN if c.isascii())
    print(f"トークン読み込み完了（{len(TOKEN)}文字）")
except FileNotFoundError:
    print("saxo_token.txt が見つかりません")
    sys.exit(1)


def get_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def find_uic(base_url, token, symbol):
    headers = get_headers(token)
    url = f"{base_url}/ref/v1/instruments"
    for params in [
        {"Keywords": symbol, "AssetTypes": "Etf"},
        {"Keywords": symbol, "AssetTypes": "Etf,Stock"},
        {"Keywords": symbol},
    ]:
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
        except Exception as e:
            print(f"  接続エラー: {e}")
            return None
        if resp.status_code != 200:
            print(f"  HTTPエラー: {resp.status_code}")
            continue
        results = resp.json().get("Data", [])
        if not results:
            continue
        for item in results:
            sym = item.get("Symbol", "")
            # "QQQ:xnas" や "QQQ" 両方に対応
            if sym == symbol or sym.split(":")[0] == symbol:
                print(f"  発見: {sym} Uic={item['Identifier']} {item['Description']}")
                return item["Identifier"]
        print(f"  候補（完全一致なし）:")
        for item in results[:5]:
            print(f"    {item.get('Symbol')} Uic={item.get('Identifier')} {item.get('Description')}")
        return None
    return None


def fetch_chart(base_url, token, uic, horizon=5, count=1200):
    headers = get_headers(token)
    url = f"{base_url}/chart/v3/charts"
    params = {
        "AssetType": "Etf", "Uic": uic, "Horizon": horizon,
        "Count": count, "Mode": "UpTo", "FieldGroups": "ChartInfo,Data,DisplayAndFormat",
    }
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
    except Exception as e:
        print(f"  接続エラー: {e}")
        return None
    if resp.status_code != 200:
        print(f"  HTTPエラー: {resp.status_code} {resp.text[:200]}")
        return None
    bars = resp.json().get("Data", [])
    if not bars:
        print("  データなし")
        return None
    return pd.DataFrame(bars)


ENVS = [
    ("シミュレーション", "https://gateway.saxobank.com/sim/openapi"),
    ("本番",             "https://gateway.saxobank.com/openapi"),
]

for env_name, base_url in ENVS:
    print(f"\n{'='*50}\n環境: {env_name}\n{'='*50}")
    print("[1] QQQ検索中...")
    uic = find_uic(base_url, TOKEN, "QQQ")
    if uic is None:
        print("  QQQ未発見。SPYで試します...")
        uic = find_uic(base_url, TOKEN, "SPY")
    if uic is None:
        print("  この環境では取得できませんでした。")
        continue
    print(f"\n[2] 5分足データ取得（Uic={uic}）...")
    df = fetch_chart(base_url, TOKEN, uic, horizon=5, count=1200)
    if df is not None:
        print(f"  取得件数: {len(df)}本")
        if "Time" in df.columns:
            t_start = pd.to_datetime(df["Time"].iloc[0])
            t_end   = pd.to_datetime(df["Time"].iloc[-1])
            days = (t_end - t_start).days
            print(f"  最古: {df['Time'].iloc[0]}")
            print(f"  最新: {df['Time'].iloc[-1]}")
            print(f"  期間: 約{days}日分")
        print(f"\n  先頭3行:\n{df.head(3).to_string()}")
        break

print("\n完了")
