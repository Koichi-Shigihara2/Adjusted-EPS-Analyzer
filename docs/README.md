# 適用が必要な 3 ファイル

ローカルにまだ反映されていません。それぞれ以下のパスに **上書きコピー** してください。

| ZIP内のパス | ローカル配置先 |
|---|---|
| `common/site-nav.js`     | `docs/common/site-nav.js`     |
| `common/site-theme.css`  | `docs/common/site-theme.css`  |
| `index.html`             | `docs/index.html`             |

## 確認方法

上書きしたら、再アクセス権限を付与してから「ローカル確認して」と言ってください。
こちらで再 grep して全て揃っているか検証します。

## 期待される結果

- `docs/common/site-nav.js` に `{ key: 'stonks', label: 'STONKS SILO', ... }` の行があること
- `docs/common/site-theme.css` に `--tool-stonks: #f43f5e` と `body[data-tool="stonks"]` があること
- `docs/index.html` の `.card-stonks` が `#f43f5e`（赤）になっていること
