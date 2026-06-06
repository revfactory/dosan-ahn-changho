/* home.js — 홈(index)
   home.json 본문(도입 서사·방식)을 렌더하고, 탐색 카드·시기 카드·검증 통계 박스를
   home.json 데이터 + meta.json 수치로 구성한다. 수치 하드코딩·재집계 금지(01_home·D-21).
   탐색/시기 카드는 home.json의 list 항목(마크다운 링크)에서 파싱 — HTML에 텍스트 박지 않음. */
import { loadAll, loadData } from './loader.js';
import { mountLayout } from './layout.js';
import { renderBlocks, makeSlotResolver, buildFigure, renderInline } from './page-render.js';
import { renderFootnotes } from './footnotes.js';

mountLayout('home');

// "**[라벨](href)** — 설명" 형태의 list item을 {label, href, desc}로 파싱
function parseLinkItem(item) {
  const m = item.match(/\*?\*?\[([^\]]+)\]\(([^)]+)\)\*?\*?\s*[—-]?\s*(.*)$/);
  if (!m) return null;
  return { label: m[1], href: m[2], desc: m[3] || '' };
}

function el(tag, cls, html) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html != null) e.innerHTML = html;
  return e;
}

function findSection(page, id) {
  return (page.sections || []).find((s) => s.id === id);
}

// v2 §10.2 통계 카운트업 — 최종값은 이미 textContent(meta.json). reduce·no-JS·비숫자('—')는
// 그대로, 숫자만 진입 시 1회 0→값. reduce면 즉시 반환(DOM의 최종값 유지).
function runCountUp(box) {
  const reduce = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const targets = Array.prototype.slice.call(box.querySelectorAll('.stat-num')).map((node) => {
    const finalText = node.textContent.trim();
    const value = parseInt(finalText, 10);
    return { node, finalText, value: Number.isNaN(value) ? null : value };
  });
  if (reduce) return;

  const durRaw = getComputedStyle(document.documentElement).getPropertyValue('--dur-count').trim();
  const dur = parseFloat(durRaw) * (durRaw.endsWith('ms') ? 1 : 1000) || 800; // 토큰값(하드코딩 금지)

  let started = false;
  const start = () => {
    if (started) return;
    started = true;
    const t0 = performance.now();
    const tick = (now) => {
      const p = Math.min(1, (now - t0) / dur);
      const eased = 1 - Math.pow(1 - p, 3); // easeOutCubic
      targets.forEach((t) => { if (t.value != null) t.node.textContent = String(Math.round(t.value * eased)); });
      if (p < 1) requestAnimationFrame(tick);
      else targets.forEach((t) => { if (t.value != null) t.node.textContent = t.finalText; });
    };
    targets.forEach((t) => { if (t.value != null) t.node.textContent = '0'; });
    requestAnimationFrame(tick);
  };

  if (!('IntersectionObserver' in window)) { start(); return; }
  const obs = new IntersectionObserver((entries, o) => {
    entries.forEach((e) => {
      if (e.isIntersecting) { start(); o.disconnect(); }
    });
  }, { threshold: 0.4 });
  obs.observe(box);
}

function firstList(section) {
  if (!section) return [];
  const b = (section.blocks || []).find((x) => x.type === 'list');
  return b ? b.items : [];
}

// 소설 진입 카드 — novel/index.json(작품 메타)에서 제목·부제·한 줄 소개를 가져와 1개 카드 구성.
// 소설은 검증 평면 밖이므로 텍스트를 하드코딩하지 않고 index.json 산출치를 쓴다.
// 소설 미빌드 시 홈을 망가뜨리지 않도록 실패는 조용히 무시(에러 UI 미표시).
async function renderNovelEntry(main) {
  let index;
  try {
    index = await loadData('data/novel/index.json');
  } catch (err) {
    return; // 소설 데이터 부재 — 보조 섹션이므로 생략(홈 본체 무영향)
  }
  const work = (index && index.work) || {};
  if (!work.title) return;

  const s = el('section', 'page-section');
  s.id = 'novel';
  s.appendChild(el('h2', 'section-heading', '소설로 읽기'));

  const card = el('a', 'nav-card home-novel-card');
  card.href = 'novel.html';
  card.appendChild(el('span', 'home-novel-kicker', '장편소설'));
  const title = el('h3', 'nav-card-title');
  title.textContent = `『${work.title}』` + (work.subtitle ? ` — ${work.subtitle}` : '');
  card.appendChild(title);
  if (work.tagline) card.appendChild(el('p', 'nav-card-desc', renderInline(work.tagline)));
  const scaleBits = [];
  if (work.unit_count) scaleBits.push(`전 ${work.unit_count}장 + 작가의 말`);
  if (scaleBits.length) card.appendChild(el('span', 'home-novel-scale', scaleBits.join(' · ')));
  s.appendChild(card);
  main.appendChild(s);
}

(async () => {
  const main = document.getElementById('app');
  try {
    const { page, meta, images, citations } = await loadAll({
      page: 'data/pages/home.json',
      meta: 'data/meta.json',
      images: 'data/images.json',
      citations: 'data/citations.json',
    });
    const slotResolver = makeSlotResolver(images);

    /* ---- 1) 히어로 (분할형: 좌 텍스트 + 우 초상, design-system §5) ---- */
    const hero = el('section', 'home-hero');
    const heroText = el('div', 'home-hero-text');
    heroText.appendChild(el('h1', 'home-hero-title', renderInline(page.title || '도산 안창호')));
    // lead 블록 중 paragraph만 히어로 텍스트로, slot은 히어로 초상으로
    (page.lead || []).forEach((b) => {
      if (b.type === 'paragraph') {
        heroText.appendChild(el('p', 'page-lead', renderInline(b.text)));
      }
    });
    hero.appendChild(heroText);
    const heroSlot = (page.lead || []).find((b) => b.type === 'slot');
    if (heroSlot) {
      const img = slotResolver(heroSlot.slot_id);
      if (img) {
        const fig = buildFigure(img, { meta: false, lazy: false });
        fig.classList.add('home-hero-figure');
        hero.appendChild(fig);
      }
    }
    main.appendChild(hero);

    /* ---- 2) 도입 서사 + 다루는 방식 (본문, 각주 대상) ---- */
    ['도입-서사', '이-사이트가-다루는-방식'].forEach((id) => {
      const sec = findSection(page, id);
      if (!sec) return;
      const s = el('section', 'page-section');
      s.id = sec.id;
      s.appendChild(el('h2', 'section-heading', renderInline(sec.heading)));
      renderBlocks(s, sec.blocks, { slotResolver });
      main.appendChild(s);
    });

    /* ---- 3) 탐색 카드 (home.json '탐색' list에서 파싱) ---- */
    const navSec = findSection(page, '탐색');
    if (navSec) {
      const s = el('section', 'page-section');
      s.id = 'explore';
      s.appendChild(el('h2', 'section-heading', renderInline(navSec.heading)));
      const grid = el('div', 'card-grid');
      firstList(navSec).forEach((item) => {
        const p = parseLinkItem(item);
        if (!p) return;
        const card = el('a', 'nav-card');
        card.href = p.href;
        card.appendChild(el('h3', 'nav-card-title', renderInline(p.label)));
        if (p.desc) card.appendChild(el('p', 'nav-card-desc', renderInline(p.desc)));
        grid.appendChild(card);
      });
      s.appendChild(grid);
      main.appendChild(s);
    }

    /* ---- 4) 여덟 시기 카드 (home.json '여덟-시기' list에서 파싱) ---- */
    const periodSec = findSection(page, '여덟-시기');
    if (periodSec) {
      const s = el('section', 'page-section');
      s.id = 'periods';
      s.appendChild(el('h2', 'section-heading', renderInline(periodSec.heading)));
      const grid = el('div', 'card-grid');
      firstList(periodSec).forEach((item) => {
        // 형태: "**P1 성장과 수학 (1878–1899)** → [1장부터](life.html#ch-01)"
        const arrow = item.split('→');
        const head = arrow[0].replace(/\*\*/g, '').trim();
        const link = arrow[1] ? parseLinkItem(arrow[1].trim()) : null;
        const codeMatch = head.match(/^(P\d)\s+(.*?)\s*\(([^)]+)\)\s*$/);
        const card = el('a', 'period-card');
        card.href = link ? link.href : '#';
        if (codeMatch) {
          card.appendChild(el('span', 'period-code', codeMatch[1]));
          card.appendChild(el('span', 'period-name', renderInline(codeMatch[2])));
          card.appendChild(el('span', 'period-years', codeMatch[3]));
        } else {
          card.appendChild(el('span', 'period-name', renderInline(head)));
        }
        grid.appendChild(card);
      });
      s.appendChild(grid);
      main.appendChild(s);
    }

    /* ---- 5) 검증 통계 박스 (meta.json 수치 — 하드코딩 금지) ---- */
    const statSec = findSection(page, '검증-통계');
    if (statSec) {
      const s = el('section', 'page-section');
      s.id = 'stats';
      s.appendChild(el('h2', 'section-heading', renderInline(statSec.heading)));
      // 섹션 도입 문단(데이터 출처 안내)도 그대로
      (statSec.blocks || []).filter((b) => b.type === 'paragraph').forEach((b, i) => {
        if (i === 0) s.appendChild(el('p', 'body-text', renderInline(b.text)));
      });
      const c = meta.counts || {};
      const cg = meta.claim_grades || {};
      const box = el('div', 'stats-box');
      const stat = (num, label) => {
        const d = el('div', 'stat');
        d.appendChild(el('span', 'stat-num', String(num)));
        d.appendChild(el('span', 'stat-label', label));
        return d;
      };
      box.appendChild(stat(c.events_rendered ?? '—', '수록 사건'));
      box.appendChild(stat(c.events_disputed ?? '—', '기록 상충'));
      box.appendChild(stat(c.claims ?? '—', '검증 주장'));
      box.appendChild(stat(c.primary_sources ?? '—', '1차 사료'));
      box.appendChild(stat(c.persons ?? '—', '인물'));
      box.appendChild(stat(c.orgs ?? '—', '조직'));
      box.appendChild(stat(c.edges ?? '—', '관계'));
      box.appendChild(stat(c.images ?? '—', '이미지'));
      const link = el('a', 'stats-link');
      link.href = 'references.html#methodology';
      link.textContent = '검증 방법론 보기';
      box.appendChild(link);
      s.appendChild(box);
      runCountUp(box); // v2 §10.2 — 진입 시 카운트업(reduce·no-JS 시 즉시 최종값)
      // 등급 분포 한 줄(meta 수치)
      if (cg.A != null) {
        s.appendChild(el('p', 'body-text',
          `주장 등급 분포 — A ${cg.A} / B ${cg.B} / C ${cg.C} / D(제외) ${cg.D}.`));
      }
      main.appendChild(s);
    }

    /* ---- 6) 소설 진입 카드 (novel/index.json — 보조 섹션, 실패 시 생략) ---- */
    await renderNovelEntry(main);

    renderFootnotes(main, citations);
  } catch (err) { /* renderLoadError가 이미 렌더 */ }
})();
