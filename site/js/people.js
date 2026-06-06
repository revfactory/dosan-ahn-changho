/* people.js — 인물 페이지
   본문(서사 8섹션)은 page-render. #graph 섹션에 vanilla SVG 관계망 그래프(nw-)를 주입한다.
   그래프 = network.json 노드 81(person+org) + 확정 엣지 135. edges_unconfirmed(19, D)는
   그래프 본체에 절대 넣지 않는다(D-04) — 미확정 목록은 페이지 데이터(#unconfirmed 표)에 이미 있음.
   라이브러리 금지(D-09). 비JS/접근 폴백 = 노드·관계 목록 테이블(<details>). */
import { loadAll } from './loader.js';
import { mountLayout } from './layout.js';
import { renderPage, makeSlotResolver } from './page-render.js';
import { renderFootnotes } from './footnotes.js';

mountLayout('people');

const SVGNS = 'http://www.w3.org/2000/svg';
const CENTER_ID = 'per-001';

// 엣지 유형 → 한글 라벨·CSS 상태 클래스(색 단독 금지: 패턴+라벨)
const EDGE_LABELS = {
  membership: '조직 소속',
  comrade: '동지',
  family: '가족',
  conflict: '갈등',
  mentor: '사제',
  patron: '후원',
};

function svg(tag, attrs) {
  const e = document.createElementNS(SVGNS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  return e;
}
function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]
  ));
}

/**
 * 결정적 레이아웃: 중심 노드(per-001)를 중앙에, 직접 연결된 1차 이웃을 안쪽 고리,
 * 나머지를 바깥 고리에 배치. 라이브러리·물리 시뮬레이션 없음(D-09).
 */
function layout(nodes, edges, W, H) {
  const cx = W / 2, cy = H / 2;
  const pos = new Map();
  const deg = new Map();
  edges.forEach((e) => {
    deg.set(e.source, (deg.get(e.source) || 0) + 1);
    deg.set(e.target, (deg.get(e.target) || 0) + 1);
  });
  const neighbors = new Set();
  edges.forEach((e) => {
    if (e.source === CENTER_ID) neighbors.add(e.target);
    if (e.target === CENTER_ID) neighbors.add(e.source);
  });

  const inner = [];
  const outer = [];
  nodes.forEach((n) => {
    if (n.id === CENTER_ID) { pos.set(n.id, { x: cx, y: cy }); return; }
    (neighbors.has(n.id) ? inner : outer).push(n);
  });
  // 안정 정렬(차수 내림차순 → id) — 결정적
  const byDeg = (a, b) => (deg.get(b.id) || 0) - (deg.get(a.id) || 0) || a.id.localeCompare(b.id);
  inner.sort(byDeg); outer.sort(byDeg);

  const rInner = Math.min(W, H) * 0.26;
  const rOuter = Math.min(W, H) * 0.46;
  const place = (arr, r) => arr.forEach((n, i) => {
    const ang = (i / Math.max(arr.length, 1)) * Math.PI * 2 - Math.PI / 2;
    pos.set(n.id, { x: cx + r * Math.cos(ang), y: cy + r * Math.sin(ang) });
  });
  place(inner, rInner);
  place(outer, rOuter);
  return { pos, deg };
}

function buildGraph(network, container) {
  const nodes = network.nodes || [];
  const edges = network.edges || []; // 확정 엣지만 — edges_unconfirmed 제외
  const nodeById = new Map(nodes.map((n) => [n.id, n]));

  const W = 900, H = 640;
  const { pos, deg } = layout(nodes, edges, W, H);

  const wrap = document.createElement('div');
  wrap.className = 'nw-graph-wrap';

  const root = svg('svg', {
    class: 'nw-graph',
    viewBox: `0 0 ${W} ${H}`,
    // NW-1: role="group"이라야 내부 노드 버튼(tabindex/role=button)이 SR 접근성 트리에 노출된다.
    // role="img"는 SVG를 원자 리프로 만들어 자식 인터랙션을 숨긴다(a11y 검증 수정안).
    role: 'group',
    'aria-label': `관계망 그래프: 인물·조직 ${nodes.length}개와 관계 ${edges.length}건. 아래 목록으로도 같은 내용을 제공합니다.`,
  });

  // 엣지 레이어
  const edgeLayer = svg('g', { class: 'nw-edge-layer' });
  edges.forEach((e, i) => {
    const a = pos.get(e.source), b = pos.get(e.target);
    if (!a || !b) return;
    const line = svg('line', {
      x1: a.x, y1: a.y, x2: b.x, y2: b.y,
      class: `nw-edge is-${e.type}`,
      'data-edge-index': i,
    });
    const sn = nodeById.get(e.source), tn = nodeById.get(e.target);
    const title = svg('title');
    title.textContent = `${sn ? sn.name : e.source} — ${tn ? tn.name : e.target} (${EDGE_LABELS[e.type] || e.type})`;
    line.appendChild(title);
    edgeLayer.appendChild(line);
  });
  root.appendChild(edgeLayer);

  // 노드 레이어
  const nodeLayer = svg('g', { class: 'nw-node-layer' });
  nodes.forEach((n) => {
    const p = pos.get(n.id);
    if (!p) return;
    const g = svg('g', {
      class: `nw-node${n.id === CENTER_ID ? ' is-center' : ''}`,
      'data-node-id': n.id,
      tabindex: '0',
      role: 'button',
      'aria-label': `${n.name}${n.hanja ? '(' + n.hanja + ')' : ''}, ${n.kind === 'org' ? '조직' : '인물'} — 상세 보기`,
      transform: `translate(${p.x},${p.y})`,
    });
    const r = Math.min(16, 8 + (deg.get(n.id) || 0) * 0.8);
    if (n.kind === 'org') {
      g.appendChild(svg('rect', { class: 'nw-node-shape', x: -r, y: -r, width: r * 2, height: r * 2, rx: 3 }));
    } else {
      g.appendChild(svg('circle', { class: 'nw-node-shape', r }));
    }
    const label = svg('text', { class: 'nw-node-label', x: 0, y: r + 10, 'text-anchor': 'middle' });
    label.textContent = n.name;
    g.appendChild(label);
    nodeLayer.appendChild(g);
  });
  root.appendChild(nodeLayer);
  wrap.appendChild(root);

  // 범례(6종, conflict 동등 비중)
  const legend = document.createElement('div');
  legend.className = 'nw-legend';
  legend.setAttribute('aria-hidden', 'false');
  legend.innerHTML =
    `<span class="nw-legend-shape">● 인물 · ■ 조직</span>` +
    Object.entries(EDGE_LABELS).map(([type, label]) =>
      `<span class="nw-legend-item"><span class="nw-legend-swatch is-${type}"></span>${esc(label)}</span>`
    ).join('');
  wrap.appendChild(legend);

  // 상세 패널
  const panel = document.createElement('div');
  panel.className = 'nw-detail-panel';
  panel.setAttribute('aria-live', 'polite');
  panel.innerHTML = '<p class="nw-empty">노드를 누르면 그 인물·조직의 정보와 관계가 표시됩니다.</p>';
  wrap.appendChild(panel);

  // 상호작용: 노드 클릭/엔터 → 패널 + 연결 엣지 하이라이트
  function showNode(id) {
    const n = nodeById.get(id);
    if (!n) return;
    // 선택 상태
    nodeLayer.querySelectorAll('.nw-node').forEach((g) =>
      g.classList.toggle('is-selected', g.getAttribute('data-node-id') === id));
    const related = edges
      .map((e, idx) => ({ e, idx }))
      .filter(({ e }) => e.source === id || e.target === id);
    const relIdx = new Set(related.map((r) => r.idx));
    edgeLayer.querySelectorAll('.nw-edge').forEach((l) =>
      l.classList.toggle('is-selected', relIdx.has(Number(l.getAttribute('data-edge-index')))));

    let html = `<h3>${esc(n.name)}${n.hanja ? `<span class="hanja">(${esc(n.hanja)})</span>` : ''}</h3>`;
    const life = [n.birth, n.death].filter(Boolean).join('–');
    if (life) html += `<p class="person-life">${esc(life)}</p>`;
    if (n.role) html += `<p>${esc(n.role)}</p>`;
    if (n.summary) html += `<p>${esc(n.summary)}</p>`;
    const anchorPage = n.kind === 'org' ? 'organizations.html' : 'people.html';
    html += `<p><a href="${anchorPage}#${esc(n.id)}">상세 위치로 이동</a></p>`;

    if (related.length) {
      html += '<p><strong>관계 ' + related.length + '건</strong></p><ul class="nw-rel-list">';
      related.forEach(({ e }) => {
        const otherId = e.source === id ? e.target : e.source;
        const other = nodeById.get(otherId);
        const evs = (e.evidence_event_ids || [])
          .map((ev) => `<a href="timeline.html#${esc(ev)}">${esc(ev)}</a>`).join(' ');
        html += `<li>${esc(other ? other.name : otherId)} <span class="src-type">${esc(EDGE_LABELS[e.type] || e.type)}</span>`
          + (evs ? ` — 근거: ${evs}` : '') + '</li>';
      });
      html += '</ul>';
    }
    panel.innerHTML = html;
  }

  nodeLayer.addEventListener('click', (ev) => {
    const g = ev.target.closest('.nw-node');
    if (g) showNode(g.getAttribute('data-node-id'));
  });
  nodeLayer.addEventListener('keydown', (ev) => {
    if (ev.key === 'Enter' || ev.key === ' ') {
      const g = ev.target.closest('.nw-node');
      if (g) { ev.preventDefault(); showNode(g.getAttribute('data-node-id')); }
    }
  });

  // 교차링크 앵커 보장(§5.2): 다른 페이지가 people.html#per-NNN 로 들어올 수 있다.
  // 본문 서사에 인라인 앵커가 없는 인물(그래프에만 등장)도 앵커가 존재해야 끊어진 링크가 0.
  // 이미 본문에 <a id="per-NNN">가 있으면 중복 추가하지 않는다.
  const anchorHost = document.createElement('div');
  anchorHost.className = 'nw-anchor-host';
  nodes.forEach((n) => {
    if (n.kind !== 'person') return; // 인물 앵커는 people 페이지가 소유(org는 organizations)
    if (document.getElementById(n.id)) return; // 본문에 이미 존재
    const a = document.createElement('span');
    a.id = n.id;
    a.className = 'nw-anchor';
    a.setAttribute('data-node-id', n.id);
    anchorHost.appendChild(a);
  });
  if (anchorHost.children.length) wrap.appendChild(anchorHost);

  // 해시로 진입 시 해당 노드 상세를 자동 표시(per-NNN)
  const selectFromHash = () => {
    const id = decodeURIComponent(location.hash.replace('#', ''));
    if (id && nodeById.has(id)) showNode(id);
  };
  window.addEventListener('hashchange', selectFromHash);
  // 초기 진입 해시 처리(렌더 직후)
  selectFromHash();

  // 비JS/접근 폴백: 노드·관계 목록 테이블(<details>) — interactive-viz 폴백 규칙
  const fallback = document.createElement('details');
  fallback.className = 'nw-fallback';
  const summary = document.createElement('summary');
  summary.textContent = '관계 목록으로 보기 (표)';
  fallback.appendChild(summary);
  const tableWrap = document.createElement('div');
  tableWrap.className = 'data-table-wrap';
  let trows = edges.map((e) => {
    const sn = nodeById.get(e.source), tn = nodeById.get(e.target);
    const evs = (e.evidence_event_ids || [])
      .map((ev) => `<a href="timeline.html#${esc(ev)}">${esc(ev)}</a>`).join(', ');
    return `<tr><td>${esc(sn ? sn.name : e.source)}</td><td>${esc(tn ? tn.name : e.target)}</td>`
      + `<td>${esc(EDGE_LABELS[e.type] || e.type)}</td><td>${evs || '—'}</td></tr>`;
  }).join('');
  tableWrap.innerHTML = `<table class="data-table"><thead><tr>`
    + `<th scope="col">대상 A</th><th scope="col">대상 B</th><th scope="col">관계</th><th scope="col">근거 사건</th>`
    + `</tr></thead><tbody>${trows}</tbody></table>`;
  fallback.appendChild(tableWrap);
  wrap.appendChild(fallback);

  container.appendChild(wrap);
}

(async () => {
  const main = document.getElementById('app');
  try {
    const { page, network, images, citations } = await loadAll({
      page: 'data/pages/people.json',
      network: 'data/network.json',
      images: 'data/images.json',
      citations: 'data/citations.json',
    });
    renderPage(main, page, {
      slotResolver: makeSlotResolver(images),
      // #graph 섹션 렌더 직후 SVG 그래프 주입(섹션의 도입 문단 다음에)
      sectionHook: (sectionEl, section) => {
        if (section.id === 'graph') buildGraph(network, sectionEl);
      },
    });
    renderFootnotes(main, citations);
  } catch (err) { /* renderLoadError가 이미 렌더 */ }
})();
