/* ==========================================================================
   novel.js — 소설 『사람을 모으는 사람』 리더 페이지
   --------------------------------------------------------------------------
   데이터: data/novel/index.json (목차 + 작품 메타) → 표지·목차 렌더.
           data/novel/ch{NN}.json·afterword.json     → 장 선택 시 lazy 로드.
   동작:   목차 클릭/URL 해시(#ch07)로 해당 장 로드, 이전/다음 내비(장 말미),
           읽던 위치 기억(localStorage — 마지막 장), 읽기 진행 바(life 패턴 재사용).
   계약:   mountLayout('novel') — 헤더·배경·skip-link·OG 자동 주입(layout.js).
           모든 데이터 로드는 loader.loadData 경유(에러 UI 일관). HTML 하드코딩 금지.
   소유:   frontend-developer. 모듈 전용 CSS는 css/novel.css(nv- 접두, D-25 패턴).
   ========================================================================== */
import { loadData } from './loader.js';
import { mountLayout } from './layout.js';

mountLayout('novel');

const STORAGE_KEY = 'dosan-novel-last-chapter';
const NOVEL_DIR = 'data/novel';

// 장 본문 JSON 메모리 캐시(같은 장 재방문 시 재요청 방지 — 단순 lazy 캐시).
const chapterCache = new Map();

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

/* ----------------------------- 표지 + 목차 ----------------------------- */

function renderCover(main, index) {
  const work = index.work || {};
  const cover = el('header', 'nv-cover');

  const kicker = el('p', 'nv-cover-kicker', '장편소설');
  cover.appendChild(kicker);

  const h1 = el('h1', 'nv-cover-title');
  h1.textContent = `『${work.title || ''}』`;
  cover.appendChild(h1);

  if (work.subtitle) cover.appendChild(el('p', 'nv-cover-subtitle', work.subtitle));
  if (work.tagline) cover.appendChild(el('p', 'nv-cover-tagline', work.tagline));

  // 작품 규모 한 줄(메타 수치 — 하드코딩 아님, index.json 산출치)
  const meta = el('p', 'nv-cover-meta');
  const bits = [];
  if (work.unit_count) bits.push(`전 ${work.unit_count}장 + 작가의 말`);
  if (index.parts) bits.push(`${(index.parts.filter((p) => p.part.startsWith('p')).length)}부 구성`);
  meta.textContent = bits.join(' · ');
  cover.appendChild(meta);

  // 검증 사이트 연결 한 줄(작가의 말 §안내와 정합 — 새 사실 생성 아님)
  const note = el('p', 'nv-cover-note');
  note.innerHTML = '이 소설이 딛고 선 검증된 기록은 ' +
    '<a href="index.html">동반 웹사이트</a>에서 사건·인물·날짜를 출처·신뢰 등급과 함께 볼 수 있습니다.';
  cover.appendChild(note);

  main.appendChild(cover);
}

function renderToc(main, index) {
  const tocById = new Map((index.toc || []).map((t) => [t.id, t]));
  const section = el('nav', 'nv-toc');
  section.setAttribute('aria-label', '목차');
  section.appendChild(el('h2', 'nv-toc-heading', '목차'));

  (index.parts || []).forEach((part) => {
    const group = el('div', 'nv-toc-group');
    group.appendChild(el('h3', 'nv-toc-part', part.name));
    const list = el('ol', 'nv-toc-list');
    (part.chapters || []).forEach((cid) => {
      const meta = tocById.get(cid);
      if (!meta) return;
      const li = el('li', 'nv-toc-item');
      const a = el('a', 'nv-toc-link');
      a.href = `#${cid}`;
      a.dataset.chapter = cid;
      a.appendChild(el('span', 'nv-toc-title', meta.title || cid));
      list.appendChild(li);
      li.appendChild(a);
    });
    group.appendChild(list);
    section.appendChild(group);
  });

  main.appendChild(section);
  return section;
}

/* ----------------------------- 장 본문 렌더 ----------------------------- */

async function fetchChapter(id) {
  if (chapterCache.has(id)) return chapterCache.get(id);
  const data = await loadData(`${NOVEL_DIR}/${id}.json`);
  chapterCache.set(id, data);
  return data;
}

// 이전/다음 내비 — 읽기 순서(toc order) 기준.
function neighbors(index, id) {
  const toc = index.toc || [];
  const i = toc.findIndex((t) => t.id === id);
  return {
    prev: i > 0 ? toc[i - 1] : null,
    next: i >= 0 && i < toc.length - 1 ? toc[i + 1] : null,
  };
}

function partName(index, partCode) {
  const p = (index.parts || []).find((x) => x.part === partCode);
  return p ? p.name : '';
}

function buildChapterNav(index, id, position) {
  const { prev, next } = neighbors(index, id);
  const nav = el('nav', `nv-chapter-nav nv-chapter-nav-${position}`);
  nav.setAttribute('aria-label', '장 이동');

  const prevWrap = el('div', 'nv-nav-slot nv-nav-prev');
  if (prev) {
    const a = el('a', 'nv-nav-link');
    a.href = `#${prev.id}`;
    a.dataset.chapter = prev.id;
    a.appendChild(el('span', 'nv-nav-dir', '이전'));
    a.appendChild(el('span', 'nv-nav-title', prev.title || prev.id));
    prevWrap.appendChild(a);
  }
  nav.appendChild(prevWrap);

  const tocWrap = el('div', 'nv-nav-slot nv-nav-toc');
  const tocLink = el('a', 'nv-nav-link nv-nav-totoc');
  tocLink.href = '#';
  tocLink.dataset.totoc = 'true';
  tocLink.textContent = '목차';
  tocWrap.appendChild(tocLink);
  nav.appendChild(tocWrap);

  const nextWrap = el('div', 'nv-nav-slot nv-nav-next');
  if (next) {
    const a = el('a', 'nv-nav-link');
    a.href = `#${next.id}`;
    a.dataset.chapter = next.id;
    a.appendChild(el('span', 'nv-nav-dir', '다음'));
    a.appendChild(el('span', 'nv-nav-title', next.title || next.id));
    nextWrap.appendChild(a);
  }
  nav.appendChild(nextWrap);

  return nav;
}

function renderChapter(reader, index, chapter) {
  reader.innerHTML = '';

  const article = el('article', 'nv-chapter');
  article.id = chapter.id;

  // 장 머리 — 부 표제 + 장 제목(부 표제와 함께, 명세)
  const head = el('header', 'nv-chapter-head');
  const pn = partName(index, chapter.part);
  if (pn && chapter.part !== 'prologue' && chapter.part !== 'epilogue' && chapter.part !== 'afterword') {
    head.appendChild(el('p', 'nv-chapter-part', pn));
  } else if (pn) {
    // 서장·종장·작가의 말은 부 표제 자체가 곧 구분명이라 별도 표기 생략(제목에 포함됨)
  }
  head.appendChild(el('h1', 'nv-chapter-title', chapter.title || chapter.id));
  article.appendChild(head);

  // 본문 — 빌드 산출 HTML(escape 완료). 상단 내비는 생략(표지/목차가 진입점), 말미만.
  const body = el('div', 'nv-body');
  body.innerHTML = chapter.html || '';
  article.appendChild(body);

  // 장 말미 내비(이전/다음/목차)
  article.appendChild(buildChapterNav(index, chapter.id, 'foot'));

  reader.appendChild(article);
}

/* --------------------------- 뷰 전환·라우팅 --------------------------- */

const view = { toc: null, reader: null, index: null };

function showToc() {
  if (view.toc) view.toc.hidden = false;
  if (view.reader) view.reader.hidden = true;
  document.body.classList.remove('nv-reading');
}

function showReader() {
  if (view.toc) view.toc.hidden = true;
  if (view.reader) view.reader.hidden = false;
  document.body.classList.add('nv-reading');
}

function markActiveToc(id) {
  if (!view.toc) return;
  view.toc.querySelectorAll('.nv-toc-link').forEach((a) => {
    a.classList.toggle('is-current', a.dataset.chapter === id);
    if (a.dataset.chapter === id) a.setAttribute('aria-current', 'true');
    else a.removeAttribute('aria-current');
  });
}

async function openChapter(id, { scroll = true } = {}) {
  if (!view.index) return;
  const exists = (view.index.toc || []).some((t) => t.id === id);
  if (!exists) { openToc(); return; }

  let chapter;
  try {
    chapter = await fetchChapter(id);
  } catch (err) {
    // loader.renderLoadError가 이미 에러 UI 렌더(빈 화면 금지)
    return;
  }
  renderChapter(view.reader, view.index, chapter);
  showReader();
  markActiveToc(id);
  try { localStorage.setItem(STORAGE_KEY, id); } catch (e) { /* 사생활 모드 등 — 무시 */ }
  updateProgress();
  if (scroll) {
    window.scrollTo({ top: 0, behavior: 'auto' });
    // 본문 첫 요소로 포커스 이동(키보드·스크린리더 — 장 전환 인지)
    const head = view.reader.querySelector('.nv-chapter-title');
    if (head) { head.setAttribute('tabindex', '-1'); head.focus({ preventScroll: true }); }
  }
}

function openToc() {
  showToc();
  markActiveToc(null);
  updateProgress();
}

// 해시 라우팅 — #ch07 형식. 빈 해시/#는 목차.
function routeFromHash() {
  const raw = (location.hash || '').replace(/^#/, '').trim();
  if (!raw) { openToc(); return; }
  openChapter(raw, { scroll: true });
}

/* ----------------------- 읽기 진행 바(life 패턴) ----------------------- */
// layout.js의 setReadProgress는 life 전용이라, novel은 동일 패턴을 자체 주입한다.
let progressBar = null;
function setupProgressBar() {
  if (document.querySelector('.read-progress')) { progressBar = document.querySelector('.read-progress'); return; }
  const bar = el('div', 'read-progress');
  bar.setAttribute('aria-hidden', 'true');
  document.body.prepend(bar);
  progressBar = bar;
  // life.js 패턴: passive 스크롤 + rAF 디바운스(레이아웃 스래시 방지).
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
  // 목차 화면에서는 진행바를 0으로(읽는 중이 아님)
  if (!document.body.classList.contains('nv-reading')) {
    progressBar.style.transform = 'scaleX(0)';
    return;
  }
  const doc = document.documentElement;
  const max = doc.scrollHeight - doc.clientHeight;
  const ratio = max > 0 ? Math.min(1, window.scrollY / max) : 0;
  progressBar.style.transform = `scaleX(${ratio})`;
}

/* ------------------------------- 부트 ------------------------------- */

(async () => {
  const main = document.getElementById('app');
  let index;
  try {
    index = await loadData(`${NOVEL_DIR}/index.json`);
  } catch (err) {
    // 에러 UI는 loader가 렌더(빈 화면 금지)
    return;
  }
  view.index = index;

  // noscript 폴백 텍스트 제거(JS 가동 확인) 후 표지·목차·리더 컨테이너 구성
  main.querySelectorAll('noscript').forEach((n) => n.remove());

  renderCover(main, index);
  view.toc = renderToc(main, index);

  view.reader = el('div', 'nv-reader');
  view.reader.hidden = true;
  main.appendChild(view.reader);

  setupProgressBar();

  // 클릭 위임 — 목차·장 내비·목차 복귀 링크. 해시 변경으로 라우팅 일원화.
  main.addEventListener('click', (e) => {
    const totoc = e.target.closest('[data-totoc]');
    if (totoc) {
      e.preventDefault();
      if (location.hash) location.hash = '';   // hashchange → routeFromHash → 목차
      else openToc();
      window.scrollTo({ top: 0, behavior: 'auto' });
      return;
    }
    const link = e.target.closest('[data-chapter]');
    if (link) {
      // 해시 변경에 라우팅을 맡긴다(딥링크·뒤로가기 일관). 기본 동작 그대로.
      return;
    }
  });

  window.addEventListener('hashchange', routeFromHash);

  // 진입 라우팅: 해시 우선 → 없으면 마지막 읽던 장 복원(localStorage) → 둘 다 없으면 목차.
  if (location.hash && location.hash !== '#') {
    routeFromHash();
  } else {
    let last = null;
    try { last = localStorage.getItem(STORAGE_KEY); } catch (e) { /* 무시 */ }
    if (last && (index.toc || []).some((t) => t.id === last)) {
      // 마지막 장을 목차 위에 "이어 읽기"로 안내(자동 점프 대신 사용자 선택 존중)
      addResumeBanner(index, last);
    }
    openToc();
  }
})();

// 이어 읽기 배너 — 표지와 목차 사이에 마지막 장으로 가는 링크 1개(자동 점프 강제 안 함).
function addResumeBanner(index, id) {
  const meta = (index.toc || []).find((t) => t.id === id);
  if (!meta || !view.toc) return;
  const banner = el('div', 'nv-resume');
  const label = el('span', 'nv-resume-label', '마지막으로 읽던 곳');
  const a = el('a', 'nv-resume-link');
  a.href = `#${id}`;
  a.dataset.chapter = id;
  a.textContent = `${meta.title || id} 이어 읽기`;
  banner.appendChild(label);
  banner.appendChild(a);
  view.toc.parentNode.insertBefore(banner, view.toc);
}
