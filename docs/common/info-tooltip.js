/* ─────────────────────────────────────────────────────────
 * On a Journey · Info Tooltip (EPIC-LEGEND-1)
 *
 * 使い方: <span data-info="glossary_key">ラベル</span>
 * を置くだけで、ⓘアイコンが自動付与され、ホバー/タップで
 * docs/common/glossary.json の該当キーの説明文がポップアップ表示される。
 *
 * 新規指標を追加する場合は glossary.json にキーを追加するだけでよい
 * （個別ページ側にツールチップHTML/CSSを書く必要はない）。
 * ───────────────────────────────────────────────────────── */
(function () {
  var SCRIPT_EL = document.currentScript || (function () {
    var list = document.getElementsByTagName('script');
    return list[list.length - 1];
  })();
  var GLOSSARY_PATH = SCRIPT_EL.src.replace(/info-tooltip\.js(\?.*)?$/, 'glossary.json');

  var STYLE = '\
    .info-trigger{cursor:help;border-bottom:1px dotted var(--mut,#94a3b8);}\
    .info-icon{display:inline-block;margin-left:3px;font-size:.85em;color:var(--acc,#3b82f6);opacity:.85;}\
    .info-tooltip-popup{\
      position:absolute;display:none;max-width:280px;z-index:1000;\
      background:var(--sur2,#161c2d);border:1px solid var(--bdr,#1f2a44);border-radius:6px;\
      padding:10px 12px;font-family:var(--sans,sans-serif);font-size:12px;line-height:1.6;\
      color:var(--txt,#e8edf5);box-shadow:0 6px 20px rgba(0,0,0,.45);\
    }\
    .info-tooltip-popup.open{display:block;}\
  ';

  function injectStyle() {
    var tag = document.createElement('style');
    tag.setAttribute('data-info-tooltip-style', '1');
    tag.textContent = STYLE;
    document.head.appendChild(tag);
  }

  var glossary = null;
  var glossaryPromise = fetch(GLOSSARY_PATH, { cache: 'no-cache' })
    .then(function (r) { return r.ok ? r.json() : {}; })
    .catch(function () { return {}; })
    .then(function (data) { glossary = data; return data; });

  var popup = null;
  function ensurePopup() {
    if (popup) return popup;
    popup = document.createElement('div');
    popup.className = 'info-tooltip-popup';
    document.body.appendChild(popup);
    return popup;
  }

  function hidePopup() {
    if (popup) { popup.classList.remove('open'); popup._target = null; }
  }

  function showPopup(target, text) {
    var p = ensurePopup();
    p.textContent = text;
    p.classList.add('open');
    p._target = target;
    var r = target.getBoundingClientRect();
    var pw = p.offsetWidth, ph = p.offsetHeight;
    var left = r.left + r.width / 2 - pw / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - pw - 8));
    var top = r.top - ph - 8;
    if (top < 8) top = r.bottom + 8;
    p.style.left = (left + window.scrollX) + 'px';
    p.style.top = (top + window.scrollY) + 'px';
  }

  function onTrigger(el) {
    var key = el.getAttribute('data-info');
    function render() {
      var text = (glossary && glossary[key]) || '（説明未登録: ' + key + '）';
      showPopup(el, text);
    }
    if (glossary) render(); else glossaryPromise.then(render);
  }

  function initTrigger(el) {
    if (el.dataset.infoInit) return;
    el.dataset.infoInit = '1';
    el.classList.add('info-trigger');
    if (!el.querySelector('.info-icon')) {
      var icon = document.createElement('span');
      icon.className = 'info-icon';
      icon.textContent = 'ⓘ'; /* ⓘ */
      el.appendChild(icon);
    }
    el.addEventListener('mouseenter', function () { onTrigger(el); });
    el.addEventListener('mouseleave', hidePopup);
    // タップ（モバイル等hoverがない環境）用。クリックでトグルすると、
    // mouseenterで既に開いた状態からの同一クリックで即閉じてしまうため、
    // トグルではなく「常に開く/位置更新」のみ行う（閉じるのはdocumentクリック/mouseleaveに任せる）
    el.addEventListener('click', function (e) {
      e.stopPropagation();
      onTrigger(el);
    });
  }

  function scan(root) {
    (root || document).querySelectorAll('[data-info]').forEach(initTrigger);
  }

  document.addEventListener('click', hidePopup);
  document.addEventListener('scroll', hidePopup, true);

  function start() {
    injectStyle();
    scan(document);
    // ページ側が非同期fetch後にinnerHTMLでテーブル/カードを描画するため、
    // 後から追加される data-info 要素も自動検出する
    var mo = new MutationObserver(function (muts) {
      for (var i = 0; i < muts.length; i++) {
        var added = muts[i].addedNodes;
        for (var j = 0; j < added.length; j++) {
          var n = added[j];
          if (n.nodeType !== 1) continue;
          if (n.matches && n.matches('[data-info]')) initTrigger(n);
          if (n.querySelectorAll) scan(n);
        }
      }
    });
    mo.observe(document.documentElement, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }

  window.InfoTooltip = { scan: scan };
})();
