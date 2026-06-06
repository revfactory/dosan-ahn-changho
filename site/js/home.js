/* home.js — 홈(index)
   home.json 본문(도입 서사·방식)을 렌더하고, 탐색 카드·시기 카드·검증 통계 박스를
   home.json 데이터 + meta.json 수치로 구성한다. 수치 하드코딩·재집계 금지(01_home·D-21).
   탐색/시기 카드는 home.json의 list 항목(마크다운 링크)에서 파싱 — HTML에 텍스트 박지 않음. */
import { loadAll } from './loader.js';
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

function firstList(section) {
  if (!section) return [];
  const b = (section.blocks || []).find((x) => x.type === 'list');
  return b ? b.items : [];
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
      // 등급 분포 한 줄(meta 수치)
      if (cg.A != null) {
        s.appendChild(el('p', 'body-text',
          `주장 등급 분포 — A ${cg.A} / B ${cg.B} / C ${cg.C} / D(제외) ${cg.D}.`));
      }
      main.appendChild(s);
    }

    renderFootnotes(main, citations);
  } catch (err) { /* renderLoadError가 이미 렌더 */ }
})();
