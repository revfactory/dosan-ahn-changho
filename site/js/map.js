/* ==========================================================================
   map.js — 활동 지도 (map-developer 소유)
   --------------------------------------------------------------------------
   계약: architecture.md §3.1(map 소비분)·§3.2·§3.7 / interactive-viz 스킬.
   - 데이터: data/timeline.json(has_geo=true만 마커) + data/pages/map.json(도입·경로해설)
     + data/citations.json(도입문·경로해설 각주, footnotes.js 후처리).
   - 외부 의존: Leaflet 1.9.x(CDN, map.html에서 로드) — 유일 허용 의존(D-10).
   - 좌표는 검증된 place 데이터만 사용. 임의 좌표 하드코딩 금지(interactive-viz §2).
     경로 폴리라인도 timeline geo 이벤트의 place 좌표를 런타임 조회해 잇는다.
   - 시기(period)는 빌드 파생 필드를 "읽기만" — 재계산 금지(§3.7·D-12).
   - 폴백: 비JS(noscript, map.html)·Leaflet 미로드·타일 실패 모두 거점 목록으로.
   - motion-reduce: 경로 표시 시 지도 이동 애니메이션을 끈다(결과 상태로 즉시 점프).
   - 공유 모듈만 import(loader·layout·footnotes) — 수정하지 않음(§4 규칙3).
   ========================================================================== */

import { loadData, renderLoadError } from './loader.js';
import { mountLayout } from './layout.js';

/* ---------------------------------------------------------------- */
/* 0. 상수·시기 정의                                                 */
/* ---------------------------------------------------------------- */

// 시기 라벨(§3.7 / sitemap §3). period 필드 값('P1'..'P8')을 읽기만 하고
// 경계 부등호는 빌드 스크립트가 단일 소유 — 여기선 표시 라벨만 보유.
const PERIODS = {
  P1: { idx: 1, label: '성장과 수학', years: '1878–1899' },
  P2: { idx: 2, label: '결혼과 1차 미주', years: '1899–1907' },
  P3: { idx: 3, label: '신민회와 망명', years: '1907–1911' },
  P4: { idx: 4, label: '2차 미주·국민회·흥사단', years: '1911–1919' },
  P5: { idx: 5, label: '임시정부와 모색', years: '1919–1924' },
  P6: { idx: 6, label: '재방문과 대독립당', years: '1924–1932' },
  P7: { idx: 7, label: '수감과 순국', years: '1932–1938' },
  P8: { idx: 8, label: '사후', years: '1938~' },
};
const PERIOD_BY_IDX = Object.fromEntries(
  Object.entries(PERIODS).map(([code, p]) => [p.idx, code])
);

// 다섯 차례의 대이동(pages/map.json map-routes와 1:1). 각 경로의 경유지는
// "지명(place.name 부분일치)"으로 timeline geo 이벤트에서 좌표를 조회한다.
// 좌표를 직접 박지 않는다 — 검증 데이터에 없는 도시는 자동으로 경로에서 빠진다
// (R1 인천항·R3 유럽 경유지는 timeline geo에 없으므로 폴리라인 미포함, 해설로만 고지).
const ROUTES = [
  { id: 'R1', label: 'R1 도미 (1902)',            waypoints: ['샌프란시스코'] },
  { id: 'R2', label: 'R2 귀국 (1907)',            waypoints: ['샌프란시스코', '도쿄', '한성(서울)'] },
  { id: 'R3', label: 'R3 망명 대장정 (1910–1911)', waypoints: ['고양군 행주', '위해위', '청도', '해삼위', '뉴욕항'] },
  { id: 'R4', label: 'R4 재방문 왕복 (1924–1926)', waypoints: ['상하이', '샌프란시스코', '상하이'] },
  { id: 'R5', label: 'R5 압송 (1932)',            waypoints: ['상하이', '한성(서울)'] },
];

const DATA_TIMELINE = 'data/timeline.json';
const DATA_PAGE = 'data/pages/map.json';
const DATA_CITATIONS = 'data/citations.json';
const DATA_NETWORK = 'data/network.json';   // place_normalization(top-level 4건, D-20)

// 지도 초기 뷰 — fitBounds로 덮어쓰므로 보수적 기본값(태평양 중심).
const INITIAL_VIEW = { center: [38, 150], zoom: 2 };

/* ---------------------------------------------------------------- */
/* 1. 유틸 (안전 DOM 생성 — innerHTML로 사용자/데이터 텍스트 주입 금지) */
/* ---------------------------------------------------------------- */

const $ = (sel, root = document) => root.querySelector(sel);

function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v == null) continue;
    if (k === 'text') node.textContent = v;
    else if (k === 'class') node.className = v;
    else if (k === 'dataset') Object.assign(node.dataset, v);
    else if (k.startsWith('aria') || k === 'role' || k === 'for') node.setAttribute(k, v);
    else node[k] = v;
  }
  for (const c of [].concat(children)) {
    if (c == null) continue;
    node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
  }
  return node;
}

const prefersReducedMotion = () =>
  !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

// map 소비 필드엔 date.start만 있으므로 ISO를 그대로 노출(정밀도 단정은 연표 권위).
function formatDate(startIso) {
  return startIso || '';
}

function liveAnnounce(msg) {
  const live = $('#map-live');
  if (live) live.textContent = msg;
}

function setTileStatus(msg) {
  const elm = $('#map-tile-status');
  if (elm) elm.textContent = msg || '';
}

/* ---------------------------------------------------------------- */
/* 2. 본문 텍스트 렌더 (안전 DOM, [ref:] 마커 보존 → footnotes 후처리) */
/* ---------------------------------------------------------------- */

// [텍스트](page.html#anchor) → <a>, **강조** → <strong>, [ref:ref-NNN] → 텍스트 보존.
// innerHTML 미사용 — 토큰 단위로 노드 생성(timeline.js renderParagraph와 동형).
function renderRichText(target, text) {
  // 1차: 마크다운 링크로 분해
  const linkRe = /\[([^\]]+)\]\(([^)]+)\)/g;
  let last = 0, m;
  const segments = [];
  while ((m = linkRe.exec(text)) !== null) {
    if (m.index > last) segments.push({ type: 'text', value: text.slice(last, m.index) });
    const label = m[1], href = m[2];
    // [ref:..] 형태는 각주 마커 — 링크로 변환하지 않고 원형 보존(§3.6 불변)
    if (/^ref:/.test(href) || /^ref:/.test(label)) {
      segments.push({ type: 'text', value: m[0] });
    } else {
      segments.push({ type: 'link', label, href });
    }
    last = linkRe.lastIndex;
  }
  if (last < text.length) segments.push({ type: 'text', value: text.slice(last) });

  // 2차: text 세그먼트 안의 **강조** 처리
  for (const seg of segments) {
    if (seg.type === 'link') {
      target.appendChild(el('a', { href: seg.href, text: seg.label }));
      continue;
    }
    const boldRe = /\*\*([^*]+)\*\*/g;
    let bLast = 0, bm;
    while ((bm = boldRe.exec(seg.value)) !== null) {
      if (bm.index > bLast) target.appendChild(document.createTextNode(seg.value.slice(bLast, bm.index)));
      target.appendChild(el('strong', { text: bm[1] }));
      bLast = boldRe.lastIndex;
    }
    if (bLast < seg.value.length) target.appendChild(document.createTextNode(seg.value.slice(bLast)));
  }
}

function renderParagraph(text) {
  const p = el('p', {});
  renderRichText(p, text);
  return p;
}

function sectionById(page, id) {
  return (page.sections || []).find((s) => s.id === id);
}

function renderLead(page) {
  if (!page) return;
  if (page.title) {
    const titleEl = $('#map-title');
    if (titleEl) titleEl.textContent = page.title;
  }
  const leadEl = $('#map-lead');
  if (!leadEl) return;
  const intro = sectionById(page, 'map-intro');
  if (!intro) return;
  const frag = document.createDocumentFragment();
  for (const b of intro.blocks || []) {
    if (b.type === 'paragraph') frag.appendChild(renderParagraph(b.text || ''));
  }
  leadEl.appendChild(frag);
}

// map-routes 섹션의 R1~R5 해설 문단을 routeId별 항목으로 렌더(전부 한 번에 생성 후 토글).
// 한 번에 렌더해야 footnotes가 모든 경로 각주를 단일 패스로 번호 매긴다.
function renderRouteCaptions(page) {
  const host = $('#map-route-caption');
  if (!host) return { note: null };
  const sec = sectionById(page, 'map-routes');
  if (!sec) return { note: null };

  let noteItem = null;
  for (const b of sec.blocks || []) {
    if (b.type !== 'paragraph') continue;
    const text = b.text || '';
    const rm = text.match(/\*\*(R\d)\b/);
    const item = el('div', { class: 'map-route-caption-item', dataset: { for: '' } });
    renderRichText(item, text);
    if (rm) {
      item.dataset.routeId = rm[1];
      item.hidden = true;            // 기본 숨김 — 경로 선택 시 해당 항목만 노출
    } else if (text.startsWith('경로선은')) {
      item.classList.add('map-route-note');
      noteItem = item;               // 공통 안내(보간 금지) — 미선택 시 노출
    } else {
      item.classList.add('map-route-note');
    }
    host.appendChild(item);
  }
  return { note: noteItem };
}

/* ---------------------------------------------------------------- */
/* 3. 거점 그룹핑 / 경로 좌표 해소                                    */
/* ---------------------------------------------------------------- */

// 같은 좌표의 여러 사건을 거점 하나로 묶는다(interactive-viz §2: 마커 하나 + 사건 목록).
function groupByPlace(events, placeNorm) {
  const groups = new Map();
  for (const e of events) {
    const key = `${e.place.lat.toFixed(4)},${e.place.lng.toFixed(4)}`;
    if (!groups.has(key)) {
      groups.set(key, { lat: e.place.lat, lng: e.place.lng, name: e.place.name, events: [] });
    }
    groups.get(key).events.push(e);
  }
  for (const g of groups.values()) {
    g.events.sort((a, b) => (a.date.start || '').localeCompare(b.date.start || ''));
    // 한 거점에 묶인 모든 사건의 지명을 대조(대표명만이 아니라 — 정규화 대상이
    // 같은 좌표의 다른 사건명에 있을 수 있다. 예: 길림 클러스터의 대동공사).
    const allNames = [...new Set(g.events.map((e) => e.place.name))];
    g.conflictNote = placeConflictNote(allNames, placeNorm);   // 지명 상충 병기(§3.3)
  }
  return [...groups.values()];
}

// 경로 waypoint(지명 부분일치)를 timeline geo 이벤트 좌표로 해소.
// 동일 지명이 여러 좌표면 사건이 가장 많은 좌표를 대표로 채택. 미확인 경유지는 건너뛴다.
function resolveRoutes(geoEvents) {
  return ROUTES.map((route) => {
    const latlngs = [];
    let missing = 0;
    for (const match of route.waypoints) {
      const cands = geoEvents.filter((e) => e.place.name.includes(match));
      if (cands.length === 0) { missing++; continue; }
      const byCoord = new Map();
      for (const e of cands) {
        const k = `${e.place.lat.toFixed(4)},${e.place.lng.toFixed(4)}`;
        byCoord.set(k, (byCoord.get(k) || 0) + 1);
      }
      const topKey = [...byCoord.entries()].sort((a, b) => b[1] - a[1])[0][0];
      const [lat, lng] = topKey.split(',').map(Number);
      latlngs.push([lat, lng]);
    }
    if (missing > 0) {
      console.warn(`[map] 경로 ${route.id}: 좌표 미확인 경유지 ${missing}건 — 해설로만 표기(보간 금지).`);
    }
    return { ...route, latlngs };
  });
}

// 지명 상충 주석(§3.3·D-20). network.json top-level place_normalization(4건)을
// 거점의 지명들과 대조해 일치 시 variants 병기 텍스트를 만든다(00_common §6 disputed 표기와 동형).
// standard 채택이 원칙이되, status="미해소"이거나 standard가 없으면 variants를 함께 노출.
// @param {string|string[]} placeNames  거점 대표명 또는 거점에 묶인 모든 지명
function placeConflictNote(placeNames, placeNorm) {
  if (!placeNames || !Array.isArray(placeNorm)) return null;
  const names = [].concat(placeNames).filter(Boolean);
  const inAny = (term) => names.some((nm) => nm.includes(term));
  for (const pn of placeNorm) {
    const all = [pn.standard, ...(pn.variants || [])].filter(Boolean);
    if (!all.some(inAny)) continue;
    const unresolved = !pn.standard || /미해소/.test(pn.status || '');
    const others = (pn.variants || []).filter((v) => !inAny(v));
    // 표기 의무: 미해소이거나, 표시명과 다른 이설이 남아 있을 때만 병기
    if (!unresolved && others.length === 0) return null;
    const variantsText = (pn.variants || []).join(' / ');
    return unresolved
      ? `지명 미해소: ${variantsText} (${pn.status || ''})`
      : `이설 병기: ${variantsText} (${pn.status || ''})`;
  }
  return null;
}

/* ---------------------------------------------------------------- */
/* 4. 거점 목록 렌더 (지도와 동등 콘텐츠 — 키보드/스크린리더 1급)      */
/* ---------------------------------------------------------------- */

// 등급 라벨 — design-system §6.1: 문자 + 라벨 텍스트 병기(색 단독 의존 금지).
// timeline.js GRADE_LABEL과 동일(두 페이지 시각 일관성, a11y CONT-2).
const GRADE_LABEL = { A: '검증', B: '학술·기관', C: '전승' };

function gradeBadge(confidence) {
  if (!confidence) return null;
  const up = String(confidence).toUpperCase();
  const g = up.toLowerCase();
  return el('span', {
    class: `grade-badge is-grade-${g}`, 'aria-label': `신뢰도 ${up}등급`,
  }, [
    el('span', { class: 'grade-letter', text: up }),
    el('span', { class: 'grade-text', text: GRADE_LABEL[up] || '' }),
  ]);
}

function eventLine(e, cls) {
  return el('li', { class: cls, dataset: { period: e.period } }, [
    el('time', { class: 'card-date', datetime: e.date.start || '', text: formatDate(e.date.start) }),
    el('span', { class: 'map-event-title', text: e.title }),
    gradeBadge(e.confidence),
    el('a', { class: 'ref-link', href: `timeline.html#${e.id}`, text: '연표에서 보기' }),
  ]);
}

function renderPlacesList(placeGroups) {
  const host = $('#map-places-list');
  if (!host) return;
  const sorted = [...placeGroups].sort((a, b) => {
    const pa = a.events[0]?.period || 'P9';
    const pb = b.events[0]?.period || 'P9';
    return pa.localeCompare(pb)
      || (a.events[0]?.date.start || '').localeCompare(b.events[0]?.date.start || '');
  });
  const frag = document.createDocumentFragment();
  for (const g of sorted) {
    const periodsHere = [...new Set(g.events.map((e) => e.period))].sort();
    const ul = el('ul', { class: 'map-place-events' }, g.events.map((e) => eventLine(e, 'map-place-event')));
    const article = el('article', {
      class: 'map-place-card', dataset: { periods: periodsHere.join(' ') },
    }, [
      el('h3', { class: 'map-place-name', text: g.name }),
      g.conflictNote ? el('p', { class: 'map-place-conflict', text: g.conflictNote }) : null,
      ul,
    ]);
    frag.appendChild(article);
  }
  host.textContent = '';
  host.appendChild(frag);
}

/* ---------------------------------------------------------------- */
/* 5. 폴백 렌더 (Leaflet 미로드·타일 실패 공용)                       */
/* ---------------------------------------------------------------- */

function renderMapFallback(reason) {
  const canvas = $('#map-canvas');
  if (canvas) {
    canvas.classList.add('is-fallback');
    canvas.textContent = '';
    const box = el('div', { class: 'map-fallback' }, [
      el('p', { class: 'map-fallback-msg', text: reason }),
      el('p', { class: 'map-fallback-hint' }, [
        '아래 ',
        el('a', { href: '#map-places-heading', text: '거점 목록' }),
        '에서 위치가 확인된 모든 사건을 시기별로 확인할 수 있습니다.',
      ]),
    ]);
    canvas.appendChild(box);
  }
  setTileStatus(reason);
}

/* ---------------------------------------------------------------- */
/* 6. Leaflet 지도 구축                                              */
/* ---------------------------------------------------------------- */

// 팝업 사건 줄: 날짜·제목·요약(있으면)·등급·연표 교차링크(design-system §6.11b).
function popupEventLine(e) {
  return el('li', { class: 'map-popup-event', dataset: { period: e.period } }, [
    el('time', { class: 'card-date', datetime: e.date.start || '', text: formatDate(e.date.start) }),
    el('span', { class: 'map-popup-title', text: e.title }),
    e.summary ? el('p', { class: 'map-popup-summary', text: e.summary }) : null,
    el('div', { class: 'map-popup-foot' }, [
      gradeBadge(e.confidence),
      el('a', { class: 'ref-link', href: `timeline.html#${e.id}`, text: '연표에서 보기' }),
    ]),
  ]);
}

function buildPopup(group) {
  const ul = el('ul', { class: 'map-popup-events' }, group.events.map(popupEventLine));
  return el('div', { class: 'map-marker-popup' }, [
    el('h4', { class: 'map-popup-place', text: group.name }),
    group.conflictNote ? el('p', { class: 'map-place-conflict', text: group.conflictNote }) : null,
    ul,
  ]);
}

function createMap(L, placeGroups, resolvedRoutes) {
  const map = L.map('map-canvas', {
    center: INITIAL_VIEW.center,
    zoom: INITIAL_VIEW.zoom,
    scrollWheelZoom: false,        // 페이지 스크롤 충돌 방지(interactive-viz §2)
    worldCopyJump: true,
  });

  // OSM 무료 타일 — attribution 의무(interactive-viz §2).
  const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> 기여자',
    maxZoom: 18,
  });
  let tileErrors = 0;
  tiles.on('tileerror', () => {
    tileErrors++;
    if (tileErrors === 4) {
      setTileStatus('지도 타일을 불러오지 못했습니다(오프라인이거나 타일 서버 차단). 거점 위치는 마커로, 전체 목록은 아래 “거점 목록”에서 볼 수 있습니다.');
    }
  });
  tiles.addTo(map);

  // --- 마커 ---
  const markerLayer = L.layerGroup().addTo(map);
  const markers = [];
  const markersByEventId = new Map();   // evt-id → 마커(딥링크 map.html#evt-NNN 해소용)
  const bounds = [];
  for (const g of placeGroups) {
    const marker = L.marker([g.lat, g.lng], {
      keyboard: true,
      alt: `거점: ${g.name} (사건 ${g.events.length}건)`,
      title: g.name,
    });
    // 팝업 내용은 DOM 노드로(지연 렌더 — 열릴 때 생성)
    marker.bindPopup(() => buildPopup(g), { className: 'map-popup-shell', maxWidth: 320 });
    marker.addTo(markerLayer);
    const rec = { marker, group: g, periods: new Set(g.events.map((e) => e.period)) };
    markers.push(rec);
    // 거점에 묶인 모든 사건 id가 같은 마커를 가리킨다(같은 좌표 = 같은 거점)
    for (const e of g.events) markersByEventId.set(e.id, rec);
    bounds.push([g.lat, g.lng]);
  }
  if (bounds.length) map.fitBounds(bounds, { padding: [40, 40], maxZoom: 5 });

  // --- 경로 폴리라인 ---
  const routeLayer = L.layerGroup().addTo(map);
  const routeLines = {};
  for (const r of resolvedRoutes) {
    if (r.latlngs.length < 2) continue;     // 점 1개는 선이 아님(R1)
    routeLines[r.id] = L.polyline(r.latlngs, {
      className: 'map-route-line', weight: 3, opacity: 0.55,
    });
  }

  // Leaflet이 컨테이너 크기를 늦게 잡는 경우 대비
  setTimeout(() => map.invalidateSize(), 0);

  return { map, markerLayer, markers, markersByEventId, routeLayer, routeLines };
}

/* ---------------------------------------------------------------- */
/* 7. 필터·경로 상호작용                                             */
/* ---------------------------------------------------------------- */

function setupInteractions(ctx, resolvedRoutes, routeNote) {
  const slider = $('#map-period-slider');
  const readout = $('#map-period-readout');
  const resetBtn = $('#map-period-reset');
  const reduceMotion = prefersReducedMotion();

  function periodLabel(idx) {
    if (idx === 0) return '전체 시기';
    const code = PERIOD_BY_IDX[idx];
    return `${code} ${PERIODS[code].label} (${PERIODS[code].years})`;
  }

  function applyPeriod(idx) {
    const code = idx === 0 ? null : PERIOD_BY_IDX[idx];
    const label = periodLabel(idx);
    if (readout) readout.textContent = label;
    if (slider) slider.setAttribute('aria-valuetext', label);
    if (resetBtn) resetBtn.hidden = idx === 0;

    // 지도 마커
    let visibleMarkers = 0;
    if (ctx && ctx.map) {
      for (const m of ctx.markers) {
        const show = code === null || m.periods.has(code);
        if (show) { if (!ctx.markerLayer.hasLayer(m.marker)) m.marker.addTo(ctx.markerLayer); visibleMarkers++; }
        else if (ctx.markerLayer.hasLayer(m.marker)) ctx.markerLayer.removeLayer(m.marker);
      }
    }

    // 거점 목록(지도 유무와 무관하게 항상 동작)
    let visibleCards = 0;
    document.querySelectorAll('.map-place-card').forEach((card) => {
      const periods = (card.dataset.periods || '').split(' ');
      const show = code === null || periods.includes(code);
      card.hidden = !show;
      if (show) visibleCards++;
      card.querySelectorAll('.map-place-event').forEach((li) => {
        li.hidden = !(code === null || li.dataset.period === code);
      });
    });

    const count = ctx && ctx.map ? visibleMarkers : visibleCards;
    liveAnnounce(`${label}. 거점 ${count}곳 표시 중.`);

    // 빈 결과 안내(경계 상황 §7)
    let emptyEl = $('#map-places-empty');
    if (visibleCards === 0) {
      if (!emptyEl) {
        emptyEl = el('p', { id: 'map-places-empty', class: 'empty-state',
          text: '해당 시기에 위치가 확인된 거점이 없습니다.' });
        $('#map-places-list')?.after(emptyEl);
      }
    } else if (emptyEl) {
      emptyEl.remove();
    }
  }

  if (slider) slider.addEventListener('input', () => applyPeriod(Number(slider.value)));
  if (resetBtn) resetBtn.addEventListener('click', () => {
    if (slider) slider.value = '0';
    applyPeriod(0);
    slider?.focus();
  });

  // --- 경로 토글 ---
  const btnHost = $('#map-route-buttons');
  let currentRoute = null;

  function showRoute(routeId) {
    const isSame = currentRoute === routeId;
    currentRoute = isSame ? null : routeId;

    btnHost?.querySelectorAll('.map-route-btn').forEach((b) => {
      const on = b.dataset.routeId === currentRoute;
      b.classList.toggle('is-current', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });

    if (ctx && ctx.map) {
      ctx.routeLayer.clearLayers();
      const line = currentRoute && ctx.routeLines[currentRoute];
      if (line) {
        line.addTo(ctx.routeLayer);
        const pathEl = line.getElement && line.getElement();
        if (pathEl) pathEl.classList.add('is-current');   // "현재 선택"만 단청
        const r = resolvedRoutes.find((x) => x.id === currentRoute);
        if (r && r.latlngs.length >= 2) {
          // motion-reduce: 애니메이션 없이 결과 상태로 즉시 점프
          ctx.map.flyToBounds(r.latlngs, {
            padding: [60, 60], maxZoom: 5,
            animate: !reduceMotion, duration: reduceMotion ? 0 : 0.6,
          });
        }
      }
    }

    // 경로 해설 캡션 토글
    document.querySelectorAll('.map-route-caption-item[data-route-id]').forEach((item) => {
      item.hidden = item.dataset.routeId !== currentRoute;
    });
    if (routeNote) routeNote.hidden = currentRoute !== null;  // 미선택 시 공통 안내 노출

    const r = resolvedRoutes.find((x) => x.id === currentRoute);
    liveAnnounce(currentRoute ? `${r ? r.label : currentRoute} 경로 표시.` : '경로 표시를 해제했습니다.');
  }

  if (btnHost) {
    const frag = document.createDocumentFragment();
    for (const r of resolvedRoutes) {
      const btn = el('button', {
        type: 'button', class: 'map-route-btn', dataset: { routeId: r.id },
        'aria-pressed': 'false', text: r.label,
      });
      if (r.latlngs.length < 2) {
        btn.title = '좌표가 확인된 경유지가 1곳뿐이라 선은 표시되지 않습니다(해설로 안내).';
      }
      frag.appendChild(btn);
    }
    btnHost.appendChild(frag);
    btnHost.addEventListener('click', (e) => {
      const btn = e.target.closest('.map-route-btn');
      if (btn) showRoute(btn.dataset.routeId);
    });
  }

  // --- 딥링크: map.html#evt-NNN (timeline "지도에서 보기" 113건의 목적지) ---
  // 해시의 evt id를 읽어 해당 마커로 이동·팝업 열기. 지도가 없으면(폴백) 거점 목록의
  // 해당 사건으로 스크롤·하이라이트. 존재하지 않는 id는 무해 처리(아무 동작 없음).
  function focusEventFromHash() {
    const raw = (location.hash || '').replace(/^#/, '');
    if (!/^evt-[A-Za-z0-9-]+$/.test(raw)) return;   // evt-id 형식만, 그 외 무시

    // 대상 사건이 시기 필터로 숨겨져 있으면 전체 보기로 풀어 노출(딥링크 우선)
    const targetCard = [...document.querySelectorAll('.map-place-event')]
      .find((li) => li.querySelector(`a[href="timeline.html#${raw}"]`));
    if (slider && slider.value !== '0') { slider.value = '0'; applyPeriod(0); }

    if (ctx && ctx.map && ctx.markersByEventId && ctx.markersByEventId.has(raw)) {
      const rec = ctx.markersByEventId.get(raw);
      // 필터로 레이어에서 빠졌을 수 있으니 보장 추가
      if (!ctx.markerLayer.hasLayer(rec.marker)) rec.marker.addTo(ctx.markerLayer);
      const ll = rec.marker.getLatLng();
      ctx.map.flyTo(ll, Math.max(ctx.map.getZoom(), 5), {
        animate: !reduceMotion, duration: reduceMotion ? 0 : 0.6,
      });
      rec.marker.openPopup();
      liveAnnounce(`${rec.group.name} 거점으로 이동했습니다.`);
    } else if (targetCard) {
      // 지도 폴백: 거점 목록의 해당 사건으로 스크롤 + 일시 하이라이트
      const card = targetCard.closest('.map-place-card');
      (card || targetCard).scrollIntoView({
        behavior: reduceMotion ? 'auto' : 'smooth', block: 'center',
      });
      targetCard.classList.add('is-deeplink-target');
      setTimeout(() => targetCard.classList.remove('is-deeplink-target'), 2400);
      liveAnnounce('거점 목록에서 해당 사건으로 이동했습니다.');
    } else {
      // 존재하지 않는 evt id 해시 — 무해. 콘솔에만 흔적.
      console.warn(`[map] 딥링크 대상 사건을 찾지 못했습니다: #${raw} (좌표 미보유이거나 미존재).`);
    }
  }

  // 초기 표시
  applyPeriod(0);

  // 다른 페이지에서의 ?period=PN 진입(연표 딥링크와 동형)
  const pq = new URLSearchParams(location.search).get('period');
  if (pq && /^P[1-8]$/.test(pq)) {
    const idx = PERIODS[pq].idx;
    if (slider) slider.value = String(idx);
    applyPeriod(idx);
  }

  // 초기 해시 딥링크 처리(?period보다 우선 — 특정 사건 노출 보장) + 이후 변경 추적
  focusEventFromHash();
  window.addEventListener('hashchange', focusEventFromHash);
}

/* ---------------------------------------------------------------- */
/* 8. 각주 후처리 (footnotes.js — 도입문 + 경로 해설)                 */
/* ---------------------------------------------------------------- */

async function applyFootnotes() {
  let citations;
  try {
    citations = await loadData(DATA_CITATIONS);
  } catch (err) {
    console.warn('[map] citations 로드 실패 — 도입문·경로 각주는 마커 텍스트로 남습니다.', err);
    return;
  }
  try {
    const { renderFootnotes } = await import('./footnotes.js');
    // 도입문과 경로 해설을 각각 후처리(각 영역 하단에 각주 목록이 붙음).
    const lead = $('#map-lead');
    const caption = $('#map-route-caption');
    if (lead) renderFootnotes(lead, citations);
    if (caption) renderFootnotes(caption, citations);
    // 도입문·캡션 각주를 지도 앱 아래로 이동(병합) — 본문보다 위에 끼지 않게 (timeline과 동일 패턴)
    const appRoot = document.getElementById('app') || document.body;
    for (const sec of document.querySelectorAll('.footnotes')) appRoot.appendChild(sec);
  } catch (err) {
    console.warn('[map] footnotes.js 미연결 — 도입문·경로 각주는 마커 텍스트로 표시됩니다.', err);
  }
}

/* ---------------------------------------------------------------- */
/* 9. 진입점                                                         */
/* ---------------------------------------------------------------- */

async function init() {
  // 헤더·내비·푸터 주입(layout.js, D-07). 데이터 로드 전에 셸을 세운다.
  try { mountLayout('map'); } catch (err) { console.warn('[map] layout 주입 실패', err); }

  let timeline, page, placeNorm = [];
  try {
    [timeline, page] = await Promise.all([
      loadData(DATA_TIMELINE),
      loadData(DATA_PAGE).catch((e) => {
        // 도입문 로드 실패는 치명 아님 — 지도 본체는 살린다.
        console.warn('[map] 도입문(pages/map.json) 로드 실패 — 지도 본체만 표시.', e);
        return null;
      }),
    ]);
  } catch (err) {
    // 연표 데이터 자체 실패 → loader가 이미 에러 UI 렌더(§3.0). 지도 영역도 폴백.
    console.error('[map] 데이터 로드 실패', err);
    renderMapFallback('데이터를 불러오지 못했습니다. 로컬 서버로 여세요: python3 -m http.server');
    return;
  }

  // 지명 상충 표기용 place_normalization(network.json top-level 4건, §3.3·D-20). 비치명.
  try {
    const net = await loadData(DATA_NETWORK);
    placeNorm = Array.isArray(net.place_normalization) ? net.place_normalization
      : (net.meta && Array.isArray(net.meta.place_normalization) ? net.meta.place_normalization : []);
  } catch (e) {
    console.warn('[map] network.json 로드 실패 — 지명 상충 병기 생략(마커는 정상).', e);
  }

  // 도입문·경로 해설
  renderLead(page);
  const { note: routeNote } = page ? renderRouteCaptions(page) : { note: null };

  // has_geo=true만 마커(§3.1 map 소비 — D 제외 후 113건). 좌표 타입도 방어 확인.
  const events = (timeline.events || []).filter((e) =>
    e.has_geo === true && e.place
    && typeof e.place.lat === 'number' && typeof e.place.lng === 'number');

  if (events.length === 0) {
    renderMapFallback('위치가 확인된 사건 데이터가 없습니다.');
    setupInteractions(null, [], routeNote);
    applyFootnotes();
    return;
  }

  const placeGroups = groupByPlace(events, placeNorm);
  const resolvedRoutes = resolveRoutes(events);

  // 거점 목록은 Leaflet 유무와 무관하게 항상 렌더(동등 콘텐츠·키보드 1급)
  renderPlacesList(placeGroups);

  // Leaflet 로드 여부 확인(map.html의 defer 스크립트가 module 전에 실행됨)
  let ctx = null;
  if (window.L && typeof window.L.map === 'function') {
    try {
      ctx = createMap(window.L, placeGroups, resolvedRoutes);
    } catch (err) {
      console.error('[map] Leaflet 지도 생성 실패', err);
      renderMapFallback('지도를 초기화하지 못했습니다. 거점 목록으로 확인하세요.');
      ctx = null;
    }
  } else {
    console.warn('[map] Leaflet 미로드 — 거점 목록 폴백으로 동작.');
    renderMapFallback('지도 라이브러리를 불러오지 못했습니다(네트워크 차단 가능). 거점 목록으로 모든 위치 보유 사건을 확인하세요.');
  }

  setupInteractions(ctx, resolvedRoutes, routeNote);

  // 도입문·경로 각주 후처리(비치명)
  applyFootnotes();

  console.info(`[map] 마커 거점 ${placeGroups.length}곳 / 위치 보유 사건 ${events.length}건 렌더.`);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
