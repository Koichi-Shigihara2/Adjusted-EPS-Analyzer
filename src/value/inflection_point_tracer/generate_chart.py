import json
import os
import matplotlib.pyplot as plt

def generate_visual_chart():
    # スクリプト自体の場所を基準に絶対パスを取得
    base_dir = os.path.dirname(__file__)
    json_path = os.path.join(base_dir, "analysis_result.json")
    output_path = os.path.join(base_dir, "analysis_chart.png")

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
    labels = ['Prior', 'Current']
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

    # 数値ラベル
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'${height:.0f}M', xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontweight='bold')

    # X-Day予測ライン
    target_x = 1 + (lag_q / 4)  
    plt.xlim(-0.5, target_x + 0.5)
    ax1.axvline(x=target_x, color='#E74C3C', linestyle='--', linewidth=2)
    ax1.text(target_x, max(revenues) * 0.5, f"🎯 Predicted X-Day\n(in {lag_q}Q)", 
             color='#E74C3C', ha='center', fontweight='bold', bbox=dict(facecolor='white', alpha=0.8))

    plt.title(f"{ticker} Inflection Forecast: {cluster}", fontsize=14, fontweight='bold')
    fig.tight_layout()
    ax1.grid(axis='y', linestyle=':', alpha=0.5)

    # 4. 指定したディレクトリへ保存
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"🎉 グラフを生成しました: {output_path}")

if __name__ == "__main__":
    generate_visual_chart()