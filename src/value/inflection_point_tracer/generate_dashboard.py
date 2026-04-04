import json
import os
from datetime import datetime

# ==========================================
# 1. パス設定
# ==========================================
base_dir = os.path.dirname(os.path.abspath(__file__))
history_path = os.path.join(base_dir, "analysis_history.json")

# 出力先を docs ディレクトリに指定
project_root = os.path.abspath(os.path.join(base_dir, "../../.."))
docs_dir = os.path.join(project_root, "docs", "value-monitor", "inflection_dashboard")
os.makedirs(docs_dir, exist_ok=True)
output_path = os.path.join(docs_dir, "index.html")

# ==========================================
# 2. 履歴データの読み込み
# ==========================================
if not os.path.exists(history_path):
    print("❌ analysis_history.json が見つかりません。")
    exit()

with open(history_path, "r", encoding="utf-8") as f:
    history_data = json.load(f)

# グラフ用のデータ配列
labels = []
revenue_data = []
cfo_data = []

# 最新のAI判定を保持する変数
latest_cluster = "不明"
latest_lag = 0

for record in history_data:
    timestamp = record.get("timestamp", "Unknown")
    labels.append(timestamp[:10]) 
    
    metrics = record.get("metrics", {})
    revenue = metrics.get("revenue", {}).get("current", 0) if isinstance(metrics, dict) else 0
    cfo = metrics.get("cfo", {}).get("current", 0) if isinstance(metrics, dict) else 0
    
    revenue_data.append(revenue)
    cfo_data.append(cfo)

    # 履歴をループしながら、常に最新のレコードの情報を上書きで取得する
    latest_cluster = record.get("cluster_name", latest_cluster)
    latest_lag = record.get("predicted_lag_q", latest_lag)

# ==========================================
# 3. HTMLの生成 (デザインを少しリッチにしました)
# ==========================================
html_template = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spidey Bot - PLTR Analysis Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
        h1 {{ text-align: center; color: #2c3e50; }}
        .stats {{ display: flex; justify-content: space-around; flex-wrap: wrap; margin-top: 20px; padding: 20px; background: #eef2f5; border-radius: 8px; gap: 10px; }}
        .stat-box {{ text-align: center; flex: 1; min-width: 150px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #2980b9; margin-top: 5px; }}
        /* AI判定パネルのスタイルを追加 */
        .info-panel {{ margin-top: 20px; padding: 15px; background: #fff3cd; border-left: 5px solid #ffc107; border-radius: 4px; font-size: 16px; line-height: 1.6; }}
        .chart-container {{ position: relative; height: 50vh; width: 100%; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 PLTR Inflection Point Tracker</h1>
        
        <div class="stats">
            <div class="stat-box">
                <div>最新の売上 (Revenue)</div>
                <div class="stat-value">${revenue_data[-1]:,.0f}</div>
            </div>
            <div class="stat-box">
                <div>最新の営業CF (CFO)</div>
                <div class="stat-value">${cfo_data[-1]:,.0f}</div>
            </div>
            <div class="stat-box">
                <div>分析実行回数</div>
                <div class="stat-value">{len(history_data)} 回</div>
            </div>
        </div>

        <!-- ここにAIの判定結果を表示します -->
        <div class="info-panel">
            <strong>🤖 AI 判定結果:</strong><br>
            事業クラスター: <strong>{latest_cluster}</strong><br>
            黒字化までの予測ラグ: <strong>{latest_lag} 四半期 (Q)</strong>
        </div>

        <div class="chart-container">
            <canvas id="metricsChart"></canvas>
        </div>
    </div>

    <script>
        const ctx = document.getElementById('metricsChart').getContext('2d');
        const metricsChart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(labels)},
                datasets: [
                    {{
                        label: 'Revenue (売上)',
                        data: {json.dumps(revenue_data)},
                        borderColor: 'rgba(52, 152, 219, 1)',
                        backgroundColor: 'rgba(52, 152, 219, 0.2)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    }},
                    {{
                        label: 'CFO (営業キャッシュフロー)',
                        data: {json.dumps(cfo_data)},
                        borderColor: 'rgba(46, 204, 113, 1)',
                        backgroundColor: 'rgba(46, 204, 113, 0.2)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{ display: true, text: 'USD' }}
                    }}
                }},
                plugins: {{
                    legend: {{ position: 'top' }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"✨ ダッシュボードを更新しました: {output_path}")