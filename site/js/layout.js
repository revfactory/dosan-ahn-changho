/* ==========================================================================
   layout.js — 공통 헤더·전역 내비·푸터 (공유 모듈, D-07)
   --------------------------------------------------------------------------
   계약: architecture.md §4 규칙6(헤더·푸터 layout.js 단일 주입, 복붙 금지)
         design-system.md §4(전역 내비 10항목·모바일 햄버거·aria-current)
   소유: frontend-developer.

   사용법(각 페이지 HTML <head> 또는 본문 스크립트에서):
     import { mountLayout } from './js/layout.js';
     mountLayout('life');   // 인자 = 현재 페이지 key(아래 NAV의 page와 일치)
   페이지 HTML에 마운트포인트가 있으면 거기에, 없으면 자동 생성한다:
     <header data-site-header></header> ... <footer data-site-footer></footer>
   ========================================================================== */

import { initReveal } from './reveal.js';

const SITE_TITLE = '도산 안창호';

// 리빌을 자체 카드 진입 모션으로 바인딩하는 모듈 페이지 — 공유 리빌 제외(소유권·중복 방지).
const REVEAL_EXCLUDED = new Set(['timeline', 'map']);

// 전역 내비 10항목 — sitemap §1 / home.json 탐색 목록과 동일 순서.
// key = 현재 페이지 판별용(파일명 stem). label = 표시명.
const NAV = [
  { key: 'home',          href: 'index.html',         label: '홈' },
  { key: 'life',          href: 'life.html',          label: '생애' },
  { key: 'timeline',      href: 'timeline.html',      label: '연표' },
  { key: 'map',           href: 'map.html',           label: '지도' },
  { key: 'organizations', href: 'organizations.html', label: '조직' },
  { key: 'philosophy',    href: 'philosophy.html',    label: '사상' },
  { key: 'people',        href: 'people.html',        label: '인물' },
  { key: 'archives',      href: 'archives.html',      label: '사료' },
  { key: 'gallery',       href: 'gallery.html',       label: '갤러리' },
  { key: 'references',    href: 'references.html',    label: '참고문헌' },
];

// 푸터 링크 — design-system.md §4(참고문헌·사료·검증 방법론 의무)
const FOOTER_LINKS = [
  { href: 'references.html', label: '참고문헌' },
  { href: 'archives.html', label: '사료 카탈로그' },
  { href: 'references.html#methodology', label: '검증 방법론' },
  { href: 'gallery.html', label: '이미지 출처' },
];

function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]
  ));
}

function buildNavItems(current) {
  return NAV.map((item) => {
    const isCurrent = item.key === current;
    const aria = isCurrent ? ' aria-current="page"' : '';
    const cls = isCurrent ? 'nav-link is-current' : 'nav-link';
    return `<li><a class="${cls}" href="${item.href}"${aria}>${esc(item.label)}</a></li>`;
  }).join('');
}

/**
 * 헤더(사이트명 + 전역 내비 10항목)와 푸터를 페이지에 주입한다.
 * 모바일 내비는 <details>로 토글(비JS 폴백 자동 충족), JS가 ESC 닫힘·aria-expanded 보강.
 * @param {string} current  현재 페이지 key (NAV의 key 중 하나)
 */
export function mountLayout(current) {
  ensureFavicon();
  ensureBgWash();
  ensureSkipLink();
  ensureOgMeta();
  mountHeader(current);
  mountFooter();
  setupStickyHeader();
  setupReadProgress(current);
  // v2 §10.2 스크롤 리빌 — 모듈 페이지(timeline/map)는 자체 바인딩이라 제외.
  if (!REVEAL_EXCLUDED.has(current)) initReveal();
}

// v2 §10.3 — life 읽기 진행 바. 상단 고정 바를 스크롤 비율로 scaleX. life에만 주입.
function setupReadProgress(current) {
  if (current !== 'life') return;
  if (document.querySelector('.read-progress')) return;
  const bar = document.createElement('div');
  bar.className = 'read-progress';
  bar.setAttribute('aria-hidden', 'true'); // 시각 보조(진행률은 스크롤바가 a11y 제공)
  document.body.prepend(bar);
  let ticking = false;
  const update = () => {
    const doc = document.documentElement;
    const max = doc.scrollHeight - doc.clientHeight;
    const ratio = max > 0 ? Math.min(1, window.scrollY / max) : 0;
    bar.style.transform = `scaleX(${ratio})`;
    ticking = false;
  };
  update();
  window.addEventListener('scroll', () => {
    if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
  }, { passive: true });
  window.addEventListener('resize', () => { window.requestAnimationFrame(update); }, { passive: true });
}

// v2 §9 — 애니메이션 배경. <body> 첫 요소로 1회 주입(favicon 단일 주입 패턴).
// 스타일·모션은 main.css(.bg-wash/.bg-blob) CSS @keyframes 전담(JS rAF 없음 — §9 성능).
function ensureBgWash() {
  if (document.querySelector('.bg-wash')) return;
  const wash = document.createElement('div');
  wash.className = 'bg-wash';
  wash.setAttribute('aria-hidden', 'true');
  // §9.1 블롭 2개 — 청자(좌상)·단청(우하). 색·크기·표류는 main.css 토큰 참조.
  wash.innerHTML =
    '<span class="bg-blob bg-blob-celadon"></span>' +
    '<span class="bg-blob bg-blob-dancheong"></span>';
  document.body.prepend(wash);
}

// v2 §10.3 — 스티키 헤더 유리 전환. JS는 .is-scrolled 토글만(전이는 main.css). passive+rAF.
function setupStickyHeader() {
  const header = document.querySelector('[data-site-header]');
  if (!header) return;
  let ticking = false;
  const update = () => {
    header.classList.toggle('is-scrolled', window.scrollY > 8);
    ticking = false;
  };
  update(); // 새로고침 시 스크롤 위치 복원 대응
  window.addEventListener('scroll', () => {
    if (!ticking) {
      ticking = true;
      window.requestAnimationFrame(update);
    }
  }, { passive: true });
}

// SEO3 — 전 페이지 OG 메타 단일 주입. **기존 title/description 텍스트만 재사용**한다
// (새 사실 문장 생성 금지 — 검증 평면 보호). 이미 og:* 태그가 있으면 추가하지 않는다.
function ensureOgMeta() {
  if (document.querySelector('meta[property^="og:"]')) return;
  const title = document.title || SITE_TITLE;
  const descEl = document.querySelector('meta[name="description"]');
  const desc = descEl ? descEl.getAttribute('content') : '';
  const tags = [
    ['og:title', title],
    ['og:type', 'website'],
    ['og:locale', 'ko_KR'],
    ['og:site_name', SITE_TITLE],
  ];
  if (desc) tags.push(['og:description', desc]);
  for (const [prop, content] of tags) {
    if (!content) continue;
    const m = document.createElement('meta');
    m.setAttribute('property', prop);
    m.setAttribute('content', content);
    document.head.appendChild(m);
  }
}

// 공통 셸 소관 — 전 페이지 skip-link 단일 주입(timeline·map 포함, BLK-2).
// a11y 권고: 타깃 id = "main", href = "#main" 고정. <main> 랜드마크에 id="main"이
// 없으면(기존 페이지는 id="app" 사용 — JS 훅) <main> 맨 앞에 <a id="main"> 앵커를
// 삽입해 #main이 본문 최상단으로 도달하게 한다(id="app" JS 훅은 보존).
// 이미 .skip-link가 있으면(정적 보유 8페이지) href만 #main으로 정규화하고 중복 추가 안 함.
function ensureSkipLink() {
  const main = document.querySelector('main');
  if (main) {
    // #main 도달 타깃 보장: main에 id가 없으면 id="main", 있으면(id="app") 내부 앵커 삽입.
    if (!document.getElementById('main')) {
      if (!main.id) {
        main.id = 'main';
        main.setAttribute('tabindex', '-1'); // 스킵 시 포커스 이동(a11y)
      } else {
        const target = document.createElement('a');
        target.id = 'main';
        target.tabIndex = -1;
        target.className = 'skip-target';
        main.prepend(target);
      }
    }
  }

  const existing = document.querySelector('.skip-link');
  if (existing) {
    existing.setAttribute('href', '#main'); // href 정규화
    return;
  }
  const link = document.createElement('a');
  link.className = 'skip-link';
  link.href = '#main';
  link.textContent = '본문 바로가기';
  document.body.prepend(link);
}

// 공통 셸 소관 — 전 페이지 favicon 단일 주입(timeline·map 포함). 404 제거.
// 디자인 토큰 범위(한지 #F7F3EB 바탕 + 단청 #B5342B '도' 마크 — design-system §1).
// HTML <head>에 이미 rel="icon"이 있으면 중복 추가하지 않는다.
function ensureFavicon() {
  if (document.querySelector('link[rel="icon"]')) return;
  const svg =
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">' +
    '<rect width="32" height="32" fill="#F7F3EB"/>' +
    '<text x="16" y="23" font-size="22" text-anchor="middle" fill="#B5342B" font-family="serif">도</text>' +
    '</svg>';
  const link = document.createElement('link');
  link.rel = 'icon';
  link.href = 'data:image/svg+xml,' + encodeURIComponent(svg);
  document.head.appendChild(link);
}

function mountHeader(current) {
  let header = document.querySelector('[data-site-header]');
  if (!header) {
    header = document.createElement('header');
    header.setAttribute('data-site-header', '');
    document.body.prepend(header);
  }
  header.className = 'site-header';
  header.innerHTML = `
    <div class="site-header-inner">
      <a class="site-brand" href="index.html">
        <span class="site-brand-name">${esc(SITE_TITLE)}</span>
        <span class="site-brand-sub">검증된 기록으로 읽는 일대기</span>
      </a>
      <nav class="site-nav" aria-label="전역 내비게이션">
        <details class="nav-toggle">
          <summary class="nav-toggle-btn" aria-label="메뉴 열기/닫기">
            <span class="nav-toggle-bars" aria-hidden="true"></span>
            <span class="nav-toggle-text">메뉴</span>
          </summary>
          <ul class="nav-list">
            ${buildNavItems(current)}
          </ul>
        </details>
      </nav>
    </div>
  `;

  // JS 보강: ESC로 모바일 메뉴 닫기 + aria-expanded 동기화(비JS 폴백은 <details> 기본 동작 유지)
  const details = header.querySelector('.nav-toggle');
  const summary = header.querySelector('.nav-toggle-btn');
  if (details && summary) {
    const syncExpanded = () => summary.setAttribute('aria-expanded', String(details.open));
    syncExpanded();
    details.addEventListener('toggle', syncExpanded);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && details.open) {
        details.open = false;
        summary.focus();
      }
    });
    // 데스크톱 폭에서는 항상 펼쳐진 상태로 보이게 하되, 토글 상태는 모바일에서만 의미.
    // 내비 링크 클릭 시 모바일 오버레이 닫기.
    header.querySelectorAll('.nav-link').forEach((a) => {
      a.addEventListener('click', () => { details.open = false; });
    });
  }
}

function mountFooter() {
  let footer = document.querySelector('[data-site-footer]');
  if (!footer) {
    footer = document.createElement('footer');
    footer.setAttribute('data-site-footer', '');
    document.body.appendChild(footer);
  }
  footer.className = 'site-footer';
  const links = FOOTER_LINKS
    .map((l) => `<li><a href="${l.href}">${esc(l.label)}</a></li>`)
    .join('');
  footer.innerHTML = `
    <div class="site-footer-inner">
      <nav class="footer-nav" aria-label="문서 링크">
        <ul class="footer-links">${links}</ul>
      </nav>
      <p class="footer-note">
        이 사이트의 모든 서술은 주장 단위 검증을 거쳤으며, 출처·등급·상충·공백을 함께 공개합니다.
        도산 안창호(島山 安昌浩, 1878–1938).
      </p>
    </div>
  `;
}
