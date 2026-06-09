/* ==========================================================================
   webtoon.js — 웹툰 『사람을 모으는 사람』 뷰어 페이지
   --------------------------------------------------------------------------
   데이터: data/webtoon/index.json (작품 메타 + 회차 목록·패널 수)
           이미지: assets/webtoon/{ep}-{NN}.jpg  (예: ep01-03.jpg)
   동작:   회차 카드 클릭/URL 해시(#ep03)로 해당 회차의 세로 스크롤 뷰 표시,
           이전/다음 회차 내비(말미), 마지막 본 회차 기억(localStorage), 진행 바.
   계약:   mountLayout('webtoon') — 헤더·배경·skip-link·OG 자동 주입(layout.js).
           모든 데이터 로드는 loader.loadData 경유(에러 UI 일관). HTML 하드코딩 금지.
           패널 이미지는 lazy 로드 + width/height 지정으로 레이아웃 시프트 방지.
   소유:   frontend-developer. 모듈 전용 CSS는 css/webtoon.css(wt- 접두).

   회차 추가: webtoon/ 에 ep{NN}-01.jpg … 를 넣고 assets/webtoon/로 복사한 뒤,
            data/webtoon/index.json 의 episodes 배열에 { id, no, title, subtitle, panels }
            한 줄을 추가하면 끝(코드 수정 불필요).
   ========================================================================== */
import { loadData } from './loader.js';
import { mountLayout } from './layout.js';

mountLayout('webtoon');

const STORAGE_KEY = 'dosan-webtoon-last-episode';
const IMG_DIR = 'assets/webtoon';

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

function pad2(n) { return String(n).padStart(2, '0'); }

function panelSrc(epId, panelNo) {
  return `${IMG_DIR}/${epId}-${pad2(panelNo)}.jpg`;
}

/* ----------------------------- 표지 + 회차 목록 ----------------------------- */

function renderCover(main, work) {
  const cover = el('header', 'wt-cover');
  cover.appendChild(el('p', 'wt-cover-kicker', '웹툰'));

  const h1 = el('h1', 'wt-cover-title');
  h1.textContent = `『${work.title || ''}』`;
  cover.appendChild(h1);

  if (work.subtitle) cover.appendChild(el('p', 'wt-cover-subtitle', work.subtitle));
  if (work.tagline) cover.appendChild(el('p', 'wt-cover-tagline', work.tagline));

  // 각색 고지 — 소설·웹툰은 검증 평면 밖(극적 재구성)임을 분명히 한다.
  if (work.note) {
    const note = el('p', 'wt-cover-note');
    note.innerHTML = work.note.replace(
      '동반 웹사이트',
      '<a href="index.html">동반 웹사이트</a>'
    );
    // note에 '동반 웹사이트' 문구가 없을 수도 있으니 링크가 안 붙으면 안내 링크를 덧붙인다.
    if (!/href=/.test(note.innerHTML)) {
      note.innerHTML += ' <a href="index.html">검증된 기록 보기</a>';
    }
    cover.appendChild(note);
  }

  // 동반 소설 안내(같은 작품의 글 버전)
  const reads = el('p', 'wt-cover-reads');
  reads.innerHTML = '같은 이야기를 글로 — <a href="novel.html">소설 『사람을 모으는 사람』</a>';
  cover.appendChild(reads);

  main.appendChild(cover);
}

function renderList(main, index) {
  const section = el('section', 'wt-list');
  section.setAttribute('aria-label', '회차 목록');
  section.appendChild(el('h2', 'wt-list-heading', '회차'));

  const grid = el('div', 'wt-ep-grid');
  (index.episodes || []).forEach((ep) => {
    const card = el('a', 'wt-ep-card');
    card.href = `#${ep.id}`;
    card.dataset.episode = ep.id;

    const thumb = el('div', 'wt-ep-thumb');
    const img = document.createElement('img');
    img.src = panelSrc(ep.id, 1);
    img.alt = `${ep.no}화 「${ep.title}」 표지 장면`;
    img.loading = 'lazy';
    img.decoding = 'async';
    img.width = index.work && index.work.panel_width || 1536;
    img.height = index.work && index.work.panel_height || 1024;
    thumb.appendChild(img);
    card.appendChild(thumb);

    const body = el('div', 'wt-ep-body');
    body.appendChild(el('span', 'wt-ep-no', `제${ep.no}화`));
    body.appendChild(el('h3', 'wt-ep-title', ep.title || ep.id));
    if (ep.subtitle) body.appendChild(el('p', 'wt-ep-subtitle', ep.subtitle));
    card.appendChild(body);

    grid.appendChild(card);
  });
  section.appendChild(grid);
  main.appendChild(section);
  return section;
}

/* ----------------------------- 회차 뷰(세로 스크롤) ----------------------------- */

function episodeById(index, id) {
  return (index.episodes || []).find((e) => e.id === id) || null;
}

function neighbors(index, id) {
  const eps = index.episodes || [];
  const i = eps.findIndex((e) => e.id === id);
  return {
    prev: i > 0 ? eps[i - 1] : null,
    next: i >= 0 && i < eps.length - 1 ? eps[i + 1] : null,
  };
}

function buildEpisodeNav(index, ep, position) {
  const { prev, next } = neighbors(index, ep.id);
  const nav = el('nav', `wt-ep-nav wt-ep-nav-${position}`);
  nav.setAttribute('aria-label', '회차 이동');

  const prevWrap = el('div', 'wt-nav-slot wt-nav-prev');
  if (prev) {
    const a = el('a', 'wt-nav-link');
    a.href = `#${prev.id}`;
    a.dataset.episode = prev.id;
    a.appendChild(el('span', 'wt-nav-dir', '이전 회차'));
    a.appendChild(el('span', 'wt-nav-title', `${prev.no}화 ${prev.title || ''}`));
    prevWrap.appendChild(a);
  }
  nav.appendChild(prevWrap);

  const listWrap = el('div', 'wt-nav-slot wt-nav-list');
  const listLink = el('a', 'wt-nav-link wt-nav-tolist', '회차 목록');
  listLink.href = '#';
  listLink.dataset.tolist = 'true';
  listWrap.appendChild(listLink);
  nav.appendChild(listWrap);

  const nextWrap = el('div', 'wt-nav-slot wt-nav-next');
  if (next) {
    const a = el('a', 'wt-nav-link');
    a.href = `#${next.id}`;
    a.dataset.episode = next.id;
    a.appendChild(el('span', 'wt-nav-dir', '다음 회차'));
    a.appendChild(el('span', 'wt-nav-title', `${next.no}화 ${next.title || ''}`));
    nextWrap.appendChild(a);
  }
  nav.appendChild(nextWrap);

  return nav;
}

function renderEpisode(reader, index, ep) {
  reader.innerHTML = '';
  const article = el('article', 'wt-episode');
  article.id = ep.id;

  const head = el('header', 'wt-episode-head');
  head.appendChild(el('p', 'wt-episode-no', `제${ep.no}화`));
  head.appendChild(el('h1', 'wt-episode-title', ep.title || ep.id));
  if (ep.subtitle) head.appendChild(el('p', 'wt-episode-subtitle', ep.subtitle));
  article.appendChild(head);

  // 세로 스크롤 패널 — 패널 사이 간격 없이 이어 붙인 웹툰 스트립.
  const strip = el('div', 'wt-strip');
  const total = ep.panels || 0;
  const w = (index.work && index.work.panel_width) || 1536;
  const h = (index.work && index.work.panel_height) || 1024;
  for (let n = 1; n <= total; n += 1) {
    const img = document.createElement('img');
    img.className = 'wt-panel';
    img.src = panelSrc(ep.id, n);
    img.alt = `${ep.title || ep.id} — 장면 ${n} / ${total}`;
    // 첫 두 장면은 즉시(eager) 로드해 진입 체감 속도 확보, 나머지는 lazy.
    img.loading = n <= 2 ? 'eager' : 'lazy';
    img.decoding = 'async';
    img.width = w;
    img.height = h;
    strip.appendChild(img);
  }
  article.appendChild(strip);

  article.appendChild(buildEpisodeNav(index, ep, 'foot'));
  reader.appendChild(article);
}

/* --------------------------- 뷰 전환·라우팅 --------------------------- */

const view = { list: null, reader: null, index: null };

function showList() {
  if (view.list) view.list.hidden = false;
  if (view.reader) view.reader.hidden = true;
  document.body.classList.remove('wt-reading');
}

function showReader() {
  if (view.list) view.list.hidden = true;
  if (view.reader) view.reader.hidden = false;
  document.body.classList.add('wt-reading');
}

function markActive(id) {
  if (!view.list) return;
  view.list.querySelectorAll('.wt-ep-card').forEach((a) => {
    const on = a.dataset.episode === id;
    a.classList.toggle('is-current', on);
    if (on) a.setAttribute('aria-current', 'true');
    else a.removeAttribute('aria-current');
  });
}

function openEpisode(id, { scroll = true } = {}) {
  if (!view.index) return;
  const ep = episodeById(view.index, id);
  if (!ep) { openList(); return; }

  renderEpisode(view.reader, view.index, ep);
  showReader();
  markActive(id);
  try { localStorage.setItem(STORAGE_KEY, id); } catch (e) { /* 사생활 모드 등 — 무시 */ }
  updateProgress();
  if (scroll) {
    window.scrollTo({ top: 0, behavior: 'auto' });
    const head = view.reader.querySelector('.wt-episode-title');
    if (head) { head.setAttribute('tabindex', '-1'); head.focus({ preventScroll: true }); }
  }
}

function openList() {
  showList();
  markActive(null);
  updateProgress();
}

function routeFromHash() {
  const raw = (location.hash || '').replace(/^#/, '').trim();
  if (!raw) { openList(); return; }
  openEpisode(raw, { scroll: true });
}

/* ----------------------- 읽기 진행 바(novel 패턴) ----------------------- */
let progressBar = null;
function setupProgressBar() {
  if (document.querySelector('.read-progress')) { progressBar = document.querySelector('.read-progress'); return; }
  const bar = el('div', 'read-progress');
  bar.setAttribute('aria-hidden', 'true');
  document.body.prepend(bar);
  progressBar = bar;
  let ticking = false;
  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(() => { updateProgress(); ticking = false; });
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
}

function updateProgress() {
  if (!progressBar) return;
  if (!document.body.classList.contains('wt-reading')) {
    progressBar.style.transform = 'scaleX(0)';
    return;
  }
  const doc = document.documentElement;
  const max = doc.scrollHeight - doc.clientHeight;
  const ratio = max > 0 ? Math.min(1, window.scrollY / max) : 0;
  progressBar.style.transform = `scaleX(${ratio})`;
}

/* ----------------------- 이어 보기 배너 ----------------------- */
function addResumeBanner(index, id) {
  const ep = episodeById(index, id);
  if (!ep || !view.list) return;
  const banner = el('div', 'wt-resume');
  banner.appendChild(el('span', 'wt-resume-label', '마지막으로 본 회차'));
  const a = el('a', 'wt-resume-link');
  a.href = `#${id}`;
  a.dataset.episode = id;
  a.textContent = `${ep.no}화 「${ep.title || id}」 이어 보기`;
  banner.appendChild(a);
  view.list.parentNode.insertBefore(banner, view.list);
}

/* ------------------------------- 부트 ------------------------------- */

(async () => {
  const main = document.getElementById('app');
  let index;
  try {
    index = await loadData('data/webtoon/index.json');
  } catch (err) {
    return; // 에러 UI는 loader가 렌더(빈 화면 금지)
  }
  view.index = index;

  main.querySelectorAll('noscript').forEach((n) => n.remove());

  renderCover(main, index.work || {});
  view.list = renderList(main, index);

  view.reader = el('div', 'wt-reader');
  view.reader.hidden = true;
  main.appendChild(view.reader);

  setupProgressBar();

  // 클릭 위임 — 회차 목록 복귀 링크만 가로챈다(회차 카드/내비는 해시 라우팅에 위임).
  main.addEventListener('click', (e) => {
    const tolist = e.target.closest('[data-tolist]');
    if (tolist) {
      e.preventDefault();
      if (location.hash) location.hash = '';
      else openList();
      window.scrollTo({ top: 0, behavior: 'auto' });
    }
  });

  window.addEventListener('hashchange', routeFromHash);

  if (location.hash && location.hash !== '#') {
    routeFromHash();
  } else {
    let last = null;
    try { last = localStorage.getItem(STORAGE_KEY); } catch (e) { /* 무시 */ }
    if (last && episodeById(index, last)) addResumeBanner(index, last);
    openList();
  }
})();
