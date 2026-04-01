import json
import os
import matplotlib.pyplot as plt

def generate_visual_chart(json_path="analysis_result.json"):
    # 1. JSONファイルの読み込み
    if not os.path.exists(json_path):
        print(f"❌ {json_path} が見つかりません。先に agent_runner.py を実行してください。")
        return
        
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    ticker = data["ticker"]
    metrics = data["metrics"]
    lag_q = data["predicted_lag_q"]
    cluster = data["cluster_name"]

    # 2. グラフ用データの整理
    labels = ['Prior (前期)', 'Current (最新期)']
    revenues = [metrics['revenue']['prior'], metrics['revenue']['current']]
    fcfs = [metrics['fcf']['prior'], metrics['fcf']['current']]

    # 3. グラフの描画
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # 棒グラフ（売上）
    color_rev = '#4A90E2'
    ax1.set_xlabel('Timeframe')
    ax1.set_ylabel('Revenue ($ Millions)', color=color_rev)
    bars = ax1.bar(labels, revenues, color=color_rev, width=0.4, alpha=0.7, label='Revenue')
    ax1.tick_params(axis='y', labelcolor=color_rev)

    # 折れ線グラフ（FCF）
    ax2 = ax1.twinx()
    color_fcf = '#2ECC71'
    ax2.set_ylabel('FCF ($ Millions)', color=color_fcf)
    ax2.plot(labels, fcfs, color=color_fcf, marker='o', markersize=8, linewidth=3, label='FCF')
    ax2.tick_params(axis='y', labelcolor=color_fcf)

    # 数値ラベルの追加
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'${height:.0f}M',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

    for i, txt in enumerate(fcfs):
        ax2.annotate(f'${txt:.0f}M', (labels[i], fcfs[i]), 
                    textcoords="offset points", xytext=(0,10), ha='center',
                    fontsize=10, fontweight='bold', color='green')

    # X-Day（タイムラグ予測）の描画
    # 「最新期」のX軸インデックスは 1 なので、そこから lag_q (4Q) を足した位置
    target_x = 1 + (lag_q / 4)  # 4Qを1年分として擬似的にX軸を伸ばす
    
    # グラフの横幅を未来側に少し広げる
    plt.xlim(-0.5, target_x + 0.5)

    # 予測の補助線を引く
    ax1.axvline(x=target_x, color='#E74C3C', linestyle='--', linewidth=2)
    ax1.text(target_x, max(revenues) * 0.5, f"🎯 予測 X-Day\n(約 {lag_q}Q 後)", 
             color='#E74C3C', ha='center', va='center', fontsize=12, fontweight='bold',
             bbox=dict(facecolor='white', alpha=0.8, edgecolor='#E74C3C'))

    # タイトルと装飾
    plt.title(f"{ticker} Financial Inflection & Forecast ({cluster})", fontsize=14, fontweight='bold')
    fig.tight_layout()
    
    # グリッド
    ax1.grid(axis='y', linestyle=':', alpha=0.5)

    # 4. 画像の保存
    chart_filename = "analysis_chart.png"
    plt.savefig(chart_filename, dpi=150)
    plt.close()
    print(f"🎉 グラフを生成し、{chart_filename} に保存しました！")

if __name__ == "__main__":
    generate_visual_chart()