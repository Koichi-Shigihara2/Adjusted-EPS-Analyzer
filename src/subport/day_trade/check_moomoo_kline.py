"""
moomoo APIで5分足データの取得可能期間を確認する
OpenDが起動している状態で実行してください。

実行:
  python check_moomoo_kline.py
"""

from moomoo import OpenQuoteContext, KLType, AuType

ctx = OpenQuoteContext(host='127.0.0.1', port=11111)

try:
    # QQQの5分足を2024年1月から取得試行
    ret, df, page_req_key = ctx.request_history_kline(
        code='US.QQQ',
        start='2024-01-01',
        end='2026-05-03',
        ktype=KLType.K_5M,
        autype=AuType.QFQ,
        max_count=1000,
    )

    if ret == 0:
        print(f"取得成功")
        print(f"件数: {len(df)}")
        print(f"最古の日付: {df['time_key'].min()}")
        print(f"最新の日付: {df['time_key'].max()}")
        print(df.head(3))
    else:
        print(f"取得失敗: {df}")

except Exception as e:
    print(f"エラー: {e}")

finally:
    ctx.close()
