/* ──────────────────────────────────────────────────────────
 * On a Journey · 統一ナビゲーション挿入
 * 各ページの <header> 内の `.nav-links` または `[data-site-nav]`
 * を見つけて、共通ナビに置き換える。
 *
 * GitHub Pages の base path（/On-a-journey/）を前提に絶対パスで構築。
 * ────────────────────────────────────────────────────────── */
(function () {
  var BASE = '/On-a-journey';

  var ITEMS = [
    { key: 'home',   label: 'ホーム',     href: BASE + '/' },
    { key: 'tanuki', label: 'TANUKI',     href: BASE + '/value-monitor/tanuki_valuation/' },
    { key: 'eps',    label: 'EPS',        href: BASE + '/value-monitor/adjusted_eps_analyzer/' },
    { key: 'mp',     label: 'MARKET',     href: BASE + '/market-monitor/market-pulse/' },
    { key: 'macro',  label: 'MACRO',      href: BASE + '/market-monitor/macro-pulse/' }
  ];

  function build(activeKey) {
    var nav = document.createElement('nav');
    nav.className = 'site-nav';
    ITEMS.forEach(function (it, i) {
      if (i > 0) {
        var sep = document.createElement('span');
        sep.className = 'nav-sep';
        nav.appendChild(sep);
      }
      var a = document.createElement('a');
      a.href = it.href;
      a.textContent = it.label;
      if (it.key === activeKey) a.className = 'active';
      nav.appendChild(a);
    });
    return nav;
  }

  function init() {
    var active = document.body.getAttribute('data-tool') || 'home';
    // 既存の .nav-links / [data-site-nav] を全部置換
    var targets = document.querySelectorAll('.nav-links, [data-site-nav]');
    targets.forEach(function (t) {
      var fresh = build(active);
      t.parentNode.replaceChild(fresh, t);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
