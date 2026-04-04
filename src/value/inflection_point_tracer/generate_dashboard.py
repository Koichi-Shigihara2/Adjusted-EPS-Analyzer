import json
import os

# ==========================================
# 1. パス設定 (shigi様の環境に合わせています)
# ==========================================
base_dir = os.path.dirname(os.path.abspath(__file__))
history_path = os.path.join(base_dir, "analysis_history.json")

# 出力先: docs/value-monitor/inflection_dashboard/index.html
project_root = os.path.abspath(os.path.join(base_dir, "../../.."))
docs_dir = os.path.join(project_root, "docs", "value-monitor", "inflection_dashboard")
os.makedirs(docs_dir, exist_ok=True)
output_path = os.path.join(docs_dir, "index.html")

# ==========================================
# 2. データの読み込みと安全策
# ==========================================
if not os.path.exists(history_path):
    print(f"❌ {history_path} が見つかりません。")
    exit()

with open(history_path, "r", encoding="utf-8") as f:
    try:
        history_data = json.load(f)
    except:
        print("❌ JSONの読み込みに失敗しました。")
        exit()

# ==========================================
# 3. HTML/JS 生成 (シミュレーター機能付き)
# ==========================================
html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Spidey Bot - Inflection Simulator</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; }
        .container { max-width: 1100px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #334155; padding-bottom: 10px; }
        .card { background: #1e293b; padding: 25px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .controls { display: flex; gap: 20px; align-items: center; background: #334155; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        select, input[type="range"] { accent-color: #38bdf8; cursor: pointer; }
        select { padding: 8px; border-radius: 5px; background: #1e293b; color: white; border: 1px solid #475569; }
        .status-badge { background: #38bdf8; color: #0f172a; padding: 4px 12px; border-radius: 20px; font-weight: bold; margin-left: 10px; }
        .chart-container { height: 550px; margin-top: 20px; }
        .info-panel { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; color: #38bdf8; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Inflection Tracker <small style="font-size: 0.5em; color: #94a3b8;">Phase 3: Step 8, 9</small></h1>
        </div>

        <div class="controls">
            <div>
                <label>対象銘柄:</label>
                <select id="stockSelector" onchange="initChart()"></select>
            </div>
            <div style="flex-grow: 1; display: flex; align-items: center; gap: 15px;">
                <label>黒字化予測ラグ (Q数): <span id="lagVal" class="status-badge">4</span></label>
                <input type="range" id="lagSlider" min="1" max="16" value="4" style="width: 100%;" oninput="updateSimulation()">
            </div>
        </div>

        <div class="card">
            <div class="info-panel">
                <div id="tickerLabel">---</div>
                <div id="runwayLabel">Runway: ---</div>
            </div>
            <div class="chart-container">
                <canvas id="simChart"></canvas>
            </div>
            <p style="font-size: 12px; color: #64748b; text-align: right; margin-top: 10px;">
                ※10-Qは年率換算(x4) | 点線はシミュレーション予測
            </p>
        </div>
    </div>

    <script>
        const rawData = """ + json.dumps(history_data) + """;
        let chart = null;

        // 銘柄リストの作成
        const tickers = [...new Set(rawData.map(d => d.ticker))];
        const selector = document.getElementById('stockSelector');
        tickers.forEach(t => { selector.add(new Option(t, t)); });

        function initChart() {
            const ticker = selector.value;
            const filtered = rawData.filter(d => d.ticker === ticker);
            const latest = filtered[filtered.length - 1];
            // 保存されているラグがあれば反映
            document.getElementById('lagSlider').value = latest.predicted_lag_q || 4;
            updateSimulation();
        }

        function updateSimulation() {
            const ticker = selector.value;
            const lag = parseInt(document.getElementById('lagSlider').value);
            document.getElementById('lagVal').innerText = lag;
            
            const filtered = rawData.filter(d => d.ticker === ticker);
            if (filtered.length === 0) return;

            // --- 1. 実績データの整理 ---
            const labels = filtered.map(d => d.timestamp.split(' ')[0] + ' (' + (d.filing_type || '10-K') + ')');
            
            // 年率換算 (10-Qは4倍)
            const revData = filtered.map(d => {
                let v = d.metrics.revenue.current || 0;
                return (d.filing_type === '10-Q') ? v * 4 : v;
            });
            const cfoData = filtered.map(d => {
                let v = d.metrics.cfo.current || 0;
                return (d.filing_type === '10-Q') ? v * 4 : v;
            });

            // --- 2. 未来予測ロジック (Step 8) ---
            const lastRev = revData[revData.length - 1];
            
            // 直近のまともなCFO（0でないもの）を起点にする
            let lastValidCfo = 0;
            for (let i = cfoData.length - 1; i >= 0; i--) {
                if (cfoData[i] !== 0) { lastValidCfo = cfoData[i]; break; }
            }

            const projLabels = [...labels];
            const projRev = [...revData];
            const projCfo = [...cfoData];

            // ラグ（Q数）に応じて未来を描画
            for (let i = 1; i <= lag; i++) {
                projLabels.push(`Q+${i} (予測)`);
                projRev.push(lastRev * Math.pow(1.05, i)); // 5%成長仮定
                // CFOが徐々にRevenueに追いつく線
                let progress = i / lag;
                projCfo.push(lastValidCfo + (lastRev - lastValidCfo) * progress);
            }

            // --- 3. Runway計算 (Step 3 暫定) ---
            let runwayMsg = "CFOプラス";
            if (lastValidCfo < 0) {
                const burn = Math.abs(lastValidCfo);
                const cashEstimate = lastRev * 0.4; // 売上の40%程度の現預金があると仮定(暫定)
                const months = (cashEstimate / burn) * 12;
                runwayMsg = `推定Runway: 約${months.toFixed(1)}ヶ月`;
            }
            document.getElementById('runwayLabel').innerText = runwayMsg;
            document.getElementById('tickerLabel').innerText = ticker + " Analysis";

            // --- 4. Chart描画 ---
            if (chart) chart.destroy();
            const ctx = document.getElementById('simChart').getContext('2d');
            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: projLabels,
                    datasets: [
                        {
                            label: 'Revenue (Annualized)',
                            data: projRev,
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            fill: true,
                            tension: 0.1
                        },
                        {
                            label: 'CFO (Annualized Projection)',
                            data: projCfo,
                            borderColor: '#10b981',
                            borderDash: [5, 5], // 点線
                            pointRadius: 4,
                            fill: false,
                            tension: 0.3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { 
                            beginAtZero: true, 
                            grid: { color: '#334155' },
                            ticks: { color: '#94a3b8', callback: v => '$' + v.toLocaleString() }
                        },
                        x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                    },
                    plugins: {
                        legend: { labels: { color: '#f8fafc' } }
                    }
                }
            });
        }
        initChart();
    </script>
</body>
</html>
"""

with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"✅ ダッシュボードを更新しました！ブラウザで確認してください。")
print(f"場所: {output_path}")