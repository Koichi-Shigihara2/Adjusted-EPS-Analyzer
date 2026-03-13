console.log("Adjusted EPS Analyzer loaded");
document.getElementById('search').addEventListener('keypress', async (e) => {
    if (e.key === 'Enter') {
        const ticker = e.target.value.toUpperCase();
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = 'Loading...';

        try {
            // data/[TICKER]/ フォルダ内の最新の結果を取得する想定
            // 本来はファイル名（アクセッション番号）の特定が必要ですが、まずはテスト用に
            const response = await fetch(`https://raw.githubusercontent.com/Koichi-Shigihara2/Adjusted-EPS-Analyzer/main/data/${ticker}/latest.json`);
            
            if (!response.ok) throw new Error('Data not found');
            
            const data = await response.json();
            resultsDiv.innerHTML = `
                <div class="result-card">
                    <h2>${ticker} Analysis</h2>
                    <p>GAAP Net Income: $${data.gaap_net_income.toLocaleString()}</p>
                    <p><strong>Adjusted EPS: $${data.adjusted_eps.toFixed(2)}</strong></p>
                </div>
            `;
        } catch (err) {
            resultsDiv.innerHTML = `<p style="color:red;">Error: ${ticker} のデータが見つかりません。GitHub Actionsが完了しているか確認してください。</p>`;
        }
    }
});
