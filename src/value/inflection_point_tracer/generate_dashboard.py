import json
import os
from datetime import datetime

# パス設定
base_dir = os.path.dirname(os.path.abspath(__file__))
history_path = os.path.join(base_dir, "analysis_history.json")
output_path = os.path.join(base_dir, "dashboard.html")

# 履歴データの読み込み
if not os.path.exists(history_path):
    print("❌ analysis_history.json が見つかりません。先に agent_runner.py を実行してください。")
    exit()

with open(history_path, "r", encoding="utf-8") as f:
    history_data = json.load(f)

# グラフ用のデータ配列を作成
labels = []
revenue_data = []
cfo_data = []

for record in history_data:
    # タイムスタンプをラベルにする（日付部分のみ抽出）
    timestamp = record.get("timestamp", "Unknown")
    labels.append(timestamp[:10]) 
    
    # metricsから数値を抽出（存在しない場合は0）
    metrics = record.get("metrics", {})
    revenue = metrics.get("revenue", {}).get("current", 0) if isinstance(metrics, dict) else 0
    cfo = metrics.get("cfo", {}).get("current", 0) if isinstance(metrics, dict) else 0
    
    revenue_data.append(revenue)
    cfo_data.append(cfo)

# HTMLとChart.jsのテンプレート
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
        .chart-container {{ position: relative; height: 50vh; width: 100%; margin-top: 30px; }}
        .stats {{ display: flex; justify-content: space-around; margin-top: 20px; padding: 20px; background: #eef2f5; border-radius: 8px; }}
        .stat-box {{ text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #2980b9; }}
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

# HTMLファイルの書き出し
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"✨ ダッシュボードを生成しました: {output_path}")
print("フォルダ内の dashboard.html をダブルクリックしてブラウザで開いてください。")