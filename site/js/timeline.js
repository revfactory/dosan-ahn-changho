/* ==========================================================================
   timeline.js — 인터랙티브 연표 (timeline-developer 소유)
   --------------------------------------------------------------------------
   계약: architecture.md §3.1(data/timeline.json)·§3.2(도입문)·§3.7(period 읽기만)·
        딥링크(§3.1 #evt-id, ?period=PN). 스킬: interactive-viz.

   ── 렌더링 전략(코드 작성 전 결정·문서화, Policy 2·계획성7) ──────────────
   • 165건은 "전체 1회 렌더 + CSS hidden 토글 필터"로 충분(스킬 §3). 가상 스크롤·
     재렌더 없음 — 측정으로 필요가 입증되기 전엔 복잡도를 사지 않는다.
   • 카드 생성은 DocumentFragment에 모아 1회 삽입(레이아웃 스래싱 회피).
   • 클릭/키 입력은 목록 컨테이너 1개에 이벤트 위임 — 리스너 수가 사건 수에
     비례하지 않게 한다.
   • 상세 패널 콘텐츠는 <dialog>에 열릴 때 지연 렌더(detail 평균 400자·최대
     1313자 × 165를 미리 DOM에 깔지 않는다).
   • 필터는 노드의 hidden 토글만 — 데이터 재렌더 없음. 결과 수는 aria-live로 고지.

   ── 데이터 정직성(Policy 4·근거성7) ──────────────────────────────────────
   • precision: day→YYYY-MM-DD, month→YYYY년 M월, year→YYYY년, range→"YYYY ~ YYYY".
     range를 단일 일자로 평탄화하지 않는다.
   • calendar=lunar: start는 양력 환산값이므로 "(양력 환산 · 원 기록 음력)"으로
     병기한다 — 표시된 양력 값을 음력이라 거짓 라벨링하지 않는다.
   • disputed: 점선 단청 테두리 + "기록 상충" 텍스트 라벨(색 단독 금지) +
     dispute_note + adopted(채택안) 우선 + variants(이설) 접기.
     adopted.precision이 null이면 사건 자신의 date를 권위로 표시.
   • confidence 배지는 항상 등급 문자 + 라벨 텍스트(색 단독 금지).
   • 출처는 구조화된 sources[]를 그대로 표시(외부 url 링크) — 추측 매핑 금지.
   • actor_refs/org_refs: node_id null→평문, non-null→people/organizations 앵커.

   ── 폴백(Policy 3·위험성향6) ─────────────────────────────────────────────
   • 비-JS: noscript 정적 안내(HTML). 데이터 로드 실패: loader.renderLoadError.
   • motion-reduce: tokens.css가 전역 0 처리 + matchMedia로 즉시 결과 상태 점프.
   • 키보드: 칩=button, 토글=checkbox, 슬라이더 없음, 패널=native dialog(트랩·Esc 무료).
   ========================================================================== */

import { loadData, renderLoadError } from './loader.js';
import { mountLayout } from './layout.js';
import { renderBlocks } from './page-render.js';

/* §3.7 시기 표(전 페이지 공통 — 표시 라벨·범위만. period 산출은 빌드 권위, 여기선 읽기만) */
const PERIODS = {
  P1: { label: '성장과 수학', range: '1878–1899' },
  P2: { label: '결혼과 1차 미주', range: '1899–1907' },
  P3: { label: '신민회와 망명', range: '1907–1911' },
  P4: { label: '2차 미주·국민회·흥사단', range: '1911–1919' },
  P5: { label: '임시정부와 모색', range: '1919–1924' },
  P6: { label: '재방문과 대독립당', range: '1924–1932' },
  P7: { label: '수감과 순국', range: '1932–1938' },
  P8: { label: '사후', range: '1938 이후' },
};
const PERIOD_ORDER = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8'];

/* 주제 태그 7종 — 데이터 그대로(병합·개명 금지, §3.1) */
const TAG_ORDER = ['결사', '이동', '사상', '가족', '교육', '언론', '연설'];

const GRADE_LABEL = { A: '검증', B: '학술·기관', C: '전승' };

const prefersReducedMotion =
  window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* 필터 상태(단일 출처) */
const state = {
  period: null,      // 'P1'.. 또는 null(전체)
  tag: null,         // 태그명 또는 null(전체)
  disputedOnly: false,
};

let allEvents = [];

/* ── 유틸: 안전한 텍스트 노드(XSS·깨진 마크업 방지) ─────────────────────── */
function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null) continue;
    if (k === 'class') node.className = v;
    else if (k === 'text') node.textContent = v;
    else if (k === 'html') node.innerHTML = v; // 신뢰 마크업만(직접 작성)
    else if (k.startsWith('data-') || k === 'role' || k.startsWith('aria-'))
      node.setAttribute(k, v);
    else node[k] = v;
  }
  for (const c of [].concat(children)) {
    if (c == null) continue;
    node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
  }
  return node;
}

/* ── 날짜 정밀도 정직 포맷(Policy 4) ──────────────────────────────────────
   start/end는 'YYYY' | 'YYYY-MM' | 'YYYY-MM-DD' 형식(빌드 보장).
*/
function parseYMD(s) {
  if (!s) return {};
  const [y, m, d] = String(s).split('-');
  return { y, m, d };
}
function fmtYear(s) {
  return `${parseYMD(s).y}년`;
}
function fmtYearMonth(s) {
  const { y, m } = parseYMD(s);
  return m ? `${y}년 ${Number(m)}월` : `${y}년`;
}
function fmtFull(s) {
  const { y, m, d } = parseYMD(s);
  if (d) return `${y}년 ${Number(m)}월 ${Number(d)}일`;
  if (m) return `${y}년 ${Number(m)}월`;
  return `${y}년`;
}
/** 사람이 읽는 날짜 라벨. precision을 데이터 그대로 표현, range는 평탄화 금지. */
function formatDate(date) {
  if (!date) return '연대 미상';
  const { start, end, precision } = date;
  switch (precision) {
    case 'day':
      return fmtFull(start);
    case 'month':
      return fmtYearMonth(start);
    case 'year':
      return fmtYear(start);
    case 'range': {
      const a = parseYMD(start).y;
      const b = parseYMD(end).y;
      // 연도가 같으면 한 해 안의 미상 시점 → 단일 연 표기, 다르면 범위
      return a && b && a !== b ? `${a} ~ ${b}년` : `${a}년`;
    }
    default:
      return start || '연대 미상';
  }
}
/** datetime 속성용 머신리더블 값(가장 정밀한 단위만). */
function machineDate(date) {
  if (!date || !date.start) return '';
  return date.precision === 'range' ? '' : date.start;
}
/** 음력 병기: start는 양력 환산값이므로 정직하게 표기(거짓 라벨 금지). */
function calendarNote(date) {
  return date && date.calendar === 'lunar' ? '양력 환산 · 원 기록 음력' : '';
}

/* ── 신뢰도 배지(색 단독 금지, design-system §6.1) ──────────────────────── */
function gradeBadge(confidence) {
  const g = (confidence || 'B').toUpperCase();
  const cls = g === 'A' ? 'is-grade-a' : g === 'C' ? 'is-grade-c' : 'is-grade-b';
  return el('span', { class: `grade-badge ${cls}`, 'aria-label': `신뢰도 ${g}등급` }, [
    el('span', { class: 'grade-letter', text: g }),
    el('span', { class: 'grade-text', text: GRADE_LABEL[g] || '' }),
  ]);
}

/* ── 카드 생성 ─────────────────────────────────────────────────────────── */
function buildCard(ev) {
  const card = el('article', {
    class: 'tl-event-card' + (ev.disputed ? ' is-disputed' : ''),
    id: ev.id, // 무변형 앵커(#evt-id 딥링크)
    'data-event-id': ev.id,
    'data-period': ev.period || '',
    'data-tags': (ev.tags || []).join('|'),
    'data-disputed': ev.disputed ? 'true' : 'false',
  });

  // disputed 라벨(색 단독 금지)
  if (ev.disputed) {
    card.appendChild(
      el('span', { class: 'disputed-flag', 'aria-label': '기록이 상충하는 사건' }, [
        el('span', { 'aria-hidden': 'true', text: '⚑ ' }),
        '기록 상충',
      ])
    );
  }

  // 날짜(정밀도 정직)
  const dateRow = el('div', {});
  const time = el('time', { class: 'tl-card-date' });
  const md = machineDate(ev.date);
  if (md) time.setAttribute('datetime', md);
  time.textContent = formatDate(ev.date);
  dateRow.appendChild(time);
  const cal = calendarNote(ev.date);
  if (cal) dateRow.appendChild(el('span', { class: 'tl-card-cal', text: `(${cal})` }));
  card.appendChild(dateRow);

  // 제목(상세 패널 여는 버튼 — 키보드 도달·작동)
  card.appendChild(
    el('button', {
      type: 'button',
      class: 'tl-card-titlebtn',
      'data-open': ev.id,
      'aria-haspopup': 'dialog',
      text: ev.title,
    })
  );

  // 요약(원문 그대로)
  if (ev.summary) card.appendChild(el('p', { class: 'tl-card-summary', text: ev.summary }));

  // 장소 메타
  if (ev.place && ev.place.name) {
    const dl = el('dl', { class: 'tl-card-meta' });
    const place = el('dd', {}, [ev.place.name]);
    if (ev.place.modern_name) {
      place.appendChild(el('span', { class: 'tl-place-modern', text: ` (${ev.place.modern_name})` }));
    }
    dl.appendChild(el('div', {}, [el('dt', { text: '장소' }), place]));
    card.appendChild(dl);
  }

  // 배지 + 주제 태그 칩
  const tagRow = el('div', { class: 'tl-card-tags' }, [gradeBadge(ev.confidence)]);
  for (const t of ev.tags || []) {
    tagRow.appendChild(el('span', { class: 'tl-tag-chip', text: t }));
  }
  card.appendChild(tagRow);

  // dispute_note(disputed 전건 동반, §3.1)
  if (ev.disputed && ev.dispute_note) {
    card.appendChild(el('p', { class: 'dispute-note', text: ev.dispute_note }));
  }

  // 카드 하단 링크: 상세 + (좌표 보유 시) 지도에서 보기
  const links = el('div', { class: 'tl-card-links' });
  links.appendChild(
    el('button', { type: 'button', class: 'tl-card-detaillink tl-reset', 'data-open': ev.id, text: '상세 보기' })
  );
  if (ev.has_geo) {
    links.appendChild(el('a', { href: `map.html#${ev.id}`, text: '지도에서 보기' }));
  }
  card.appendChild(links);

  return card;
}

/* ── 시기 그룹으로 카드 렌더(DocumentFragment 1회 삽입) ──────────────────── */
function renderList(events) {
  const list = document.getElementById('tl-list');
  const frag = document.createDocumentFragment();

  // 시기순 → 시기 내 date.start 오름차순 정렬(원본 불변, 사본 정렬)
  const byPeriod = new Map();
  for (const code of PERIOD_ORDER) byPeriod.set(code, []);
  for (const ev of events) {
    const code = byPeriod.has(ev.period) ? ev.period : 'P8';
    byPeriod.get(code).push(ev);
  }

  const jump = document.getElementById('tl-jump');
  const jumpFrag = document.createDocumentFragment();
  let renderedAny = false;

  for (const code of PERIOD_ORDER) {
    const group = byPeriod.get(code);
    if (!group.length) continue;
    renderedAny = true;
    group.sort((a, b) => String(a.date.start).localeCompare(String(b.date.start)));

    const info = PERIODS[code] || { label: code, range: '' };
    const section = el('section', {
      class: 'tl-period-group',
      id: `period-${code}`,
      'data-period-group': code,
      'aria-labelledby': `heading-${code}`,
    });
    const heading = el('h2', { class: 'tl-period-heading', id: `heading-${code}` }, [
      `${code}. ${info.label}`,
      el('span', { class: 'tl-period-range', text: info.range }),
    ]);
    section.appendChild(heading);

    const cards = el('div', { class: 'tl-group-cards' });
    for (const ev of group) cards.appendChild(buildCard(ev));
    section.appendChild(cards);
    frag.appendChild(section);

    // 시기 점프 링크
    jumpFrag.appendChild(
      el('a', { class: 'tl-jump-link', href: `#period-${code}`, 'data-jump': code,
        text: `${code} ${info.label}` })
    );
  }

  list.appendChild(frag);
  jump.appendChild(jumpFrag);
  if (renderedAny) jump.hidden = false;
}

/* ── 필터 적용(노드 hidden 토글, 재렌더 없음) ───────────────────────────── */
function applyFilters() {
  const cards = document.querySelectorAll('.tl-event-card');
  let visible = 0;
  for (const card of cards) {
    const periodOk = !state.period || card.dataset.period === state.period;
    const tagOk =
      !state.tag || (card.dataset.tags || '').split('|').includes(state.tag);
    const dispOk = !state.disputedOnly || card.dataset.disputed === 'true';
    const show = periodOk && tagOk && dispOk;
    card.hidden = !show;
    if (show) visible++;
  }

  // 빈 시기 그룹·점프 링크 숨김(빈 헤더 잔류 방지)
  document.querySelectorAll('.tl-period-group').forEach((group) => {
    const anyVisible = group.querySelector('.tl-event-card:not([hidden])');
    group.hidden = !anyVisible;
    const code = group.dataset.periodGroup;
    const jumpLink = document.querySelector(`.tl-jump-link[data-jump="${code}"]`);
    if (jumpLink) jumpLink.hidden = !anyVisible;
  });

  // 빈 상태(0건)
  const empty = document.getElementById('tl-empty');
  empty.hidden = visible !== 0;

  // 라이브 고지(스킬 §5) — 활성 필터 요약 동반
  const parts = [];
  if (state.period) parts.push(`${state.period} ${PERIODS[state.period].label}`);
  if (state.tag) parts.push(`주제 ${state.tag}`);
  if (state.disputedOnly) parts.push('기록 상충만');
  const filterTxt = parts.length ? ` (${parts.join(' · ')})` : '';
  document.getElementById('tl-status').textContent =
    visible === 0 ? `표시할 사건 없음${filterTxt}` : `사건 ${visible}건 표시 중${filterTxt}`;

  // 리셋 버튼 노출
  document.getElementById('tl-reset').hidden =
    !(state.period || state.tag || state.disputedOnly);

  syncUrl();
}

/* URL 동기화 — ?period=PN (필터 공유). 태그·disputed는 해시 오염을 피해 쿼리에 둠 */
function syncUrl() {
  const params = new URLSearchParams();
  if (state.period) params.set('period', state.period);
  if (state.tag) params.set('tag', state.tag);
  if (state.disputedOnly) params.set('disputed', '1');
  const qs = params.toString();
  const newUrl = `${location.pathname}${qs ? '?' + qs : ''}${location.hash}`;
  history.replaceState(null, '', newUrl);
}

/* ── 필터 UI(칩) 생성 ──────────────────────────────────────────────────── */
function buildFilterChips(events) {
  // 데이터에 실재하는 시기/태그만 칩 생성 + 건수 표기
  const periodCount = {};
  const tagCount = {};
  for (const ev of events) {
    if (ev.period) periodCount[ev.period] = (periodCount[ev.period] || 0) + 1;
    for (const t of ev.tags || []) tagCount[t] = (tagCount[t] || 0) + 1;
  }

  const periodWrap = document.getElementById('tl-period-filter');
  periodWrap.appendChild(makeChip('전체', null, 'period', events.length, true));
  for (const code of PERIOD_ORDER) {
    if (!periodCount[code]) continue;
    periodWrap.appendChild(
      makeChip(`${code} ${PERIODS[code].label}`, code, 'period', periodCount[code], false)
    );
  }

  const tagWrap = document.getElementById('tl-tag-filter');
  tagWrap.appendChild(makeChip('전체', null, 'tag', events.length, true));
  for (const t of TAG_ORDER) {
    if (!tagCount[t]) continue;
    tagWrap.appendChild(makeChip(t, t, 'tag', tagCount[t], false));
  }
}
function makeChip(label, value, kind, count, active) {
  const btn = el('button', {
    type: 'button',
    class: 'tl-chip' + (active ? ' is-active' : ''),
    'data-filter': kind,
    'data-value': value == null ? '' : value,
    'aria-pressed': active ? 'true' : 'false',
  }, [label]);
  if (count != null) btn.appendChild(el('span', { class: 'tl-chip-count', text: String(count) }));
  return btn;
}
function setChipActive(kind, value) {
  document.querySelectorAll(`.tl-chip[data-filter="${kind}"]`).forEach((chip) => {
    const on = (chip.dataset.value || '') === (value || '');
    chip.classList.toggle('is-active', on);
    chip.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
}

/* ── 상세 패널(지연 렌더 + native dialog) ──────────────────────────────── */
const dialog = () => document.getElementById('tl-detail');
let lastFocused = null;

function openDetail(eventId) {
  const ev = allEvents.find((e) => e.id === eventId);
  if (!ev) return;
  lastFocused = document.activeElement;
  renderDetail(ev);
  const dlg = dialog();
  if (typeof dlg.showModal === 'function') dlg.showModal();
  else dlg.setAttribute('open', ''); // 구형 폴백
}

function renderDetail(ev) {
  const body = document.getElementById('tl-detail-body');
  body.textContent = ''; // 이전 내용 비우기(지연 렌더)
  const frag = document.createDocumentFragment();

  // 날짜 + 음력 병기
  const dateLine = el('p', { class: 'tl-detail-date' }, [formatDate(ev.date)]);
  const cal = calendarNote(ev.date);
  if (cal) dateLine.appendChild(el('span', { class: 'tl-card-cal', text: ` (${cal})` }));
  frag.appendChild(dateLine);

  // 제목
  frag.appendChild(el('h2', { class: 'tl-detail-title', id: 'tl-detail-title', text: ev.title }));

  // 신뢰도 배지 + disputed 라벨
  const badges = el('div', { class: 'tl-card-tags' }, [gradeBadge(ev.confidence)]);
  if (ev.disputed) {
    badges.appendChild(
      el('span', { class: 'disputed-flag', 'aria-label': '기록이 상충하는 사건' }, ['⚑ 기록 상충'])
    );
  }
  frag.appendChild(badges);

  // 상세 본문(detail의 \n 보존)
  if (ev.detail) {
    frag.appendChild(el('h3', { text: '상세' }));
    frag.appendChild(el('p', { class: 'tl-detail-text', text: ev.detail }));
  } else if (ev.summary) {
    frag.appendChild(el('p', { class: 'tl-detail-text', text: ev.summary }));
  }

  // 기록 상충: adopted(채택안) 우선 + variants(이설) 접기
  if (ev.disputed && ev.dispute) frag.appendChild(renderDispute(ev));

  // 장소
  if (ev.place && ev.place.name) {
    frag.appendChild(el('h3', { text: '장소' }));
    const placeP = el('p', {}, [ev.place.name]);
    if (ev.place.modern_name) placeP.appendChild(el('span', { class: 'tl-place-modern', text: ` (${ev.place.modern_name})` }));
    frag.appendChild(placeP);
  }

  // 관련 인물·조직(node_id null=평문, non-null=앵커)
  const refs = renderRefs(ev);
  if (refs) frag.appendChild(refs);

  // 출처(구조화 sources[] 직접 표시 — 추측 매핑 금지)
  if (ev.sources && ev.sources.length) {
    frag.appendChild(el('h3', { text: `출처 ${ev.sources.length}건` }));
    frag.appendChild(renderSources(ev.sources));
  }

  // 교차 동선: 지도(좌표 보유 시) + id raw
  const cross = el('div', { class: 'tl-detail-crosslinks' });
  if (ev.has_geo) cross.appendChild(el('a', { href: `map.html#${ev.id}`, text: '지도에서 보기' }));
  cross.appendChild(el('span', { class: 'tl-id-raw', text: ev.id }));
  frag.appendChild(cross);

  body.appendChild(frag);
}

function renderDispute(ev) {
  const dp = ev.dispute;
  const box = el('section', { class: 'tl-dispute-box', 'aria-label': '기록 상충 — 양론 병기' });
  if (dp.status) box.appendChild(el('p', { class: 'tl-dispute-status', text: `상충 상태: ${dp.status}` }));

  // 채택안(adopted) — precision이 null이면 날짜가 아닌 사실/위치 상충이므로
  // 사건 자신의 date를 권위로, claim/basis를 설명으로 표시.
  const ad = dp.adopted || {};
  const adoptedBox = el('p', { class: 'tl-dispute-adopted' });
  adoptedBox.appendChild(el('span', { class: 'tl-adopted-label', text: '채택: ' }));
  if (ad.precision) {
    // 날짜 채택안 — adopted의 start/end/precision으로 표기
    adoptedBox.appendChild(document.createTextNode(formatDate(ad)));
    if (ad.basis) adoptedBox.appendChild(el('span', { class: 'tl-variant-assess', text: ` — ${ad.basis}` }));
  } else {
    // 날짜 외 상충(사실·위치) — claim 텍스트 + basis
    adoptedBox.appendChild(document.createTextNode(ad.claim || formatDate(ev.date)));
    if (ad.basis) adoptedBox.appendChild(el('span', { class: 'tl-variant-assess', text: ` — ${ad.basis}` }));
  }
  box.appendChild(adoptedBox);

  // 이설(variants) — 접기. adopted를 확정처럼 보이지 않게 이설을 함께 보존.
  const variants = dp.variants || [];
  if (variants.length) {
    const det = el('details', { class: 'tl-dispute-variants' });
    det.appendChild(el('summary', { text: `다른 기록 ${variants.length}건 보기` }));
    const ul = el('ul', {});
    for (const v of variants) {
      const li = el('li', {}, [v.claim || '']);
      const meta = [];
      if (v.source) meta.push(v.source);
      if (v.assessment) meta.push(v.assessment);
      if (meta.length) li.appendChild(el('span', { class: 'tl-variant-assess', text: ` (${meta.join(' · ')})` }));
      ul.appendChild(li);
    }
    det.appendChild(ul);
    box.appendChild(det);
  }
  return box;
}

function renderRefs(ev) {
  const actors = ev.actor_refs || [];
  const orgs = ev.org_refs || [];
  if (!actors.length && !orgs.length) return null;
  const wrap = document.createDocumentFragment();

  if (actors.length) {
    wrap.appendChild(el('h3', { text: '관련 인물' }));
    wrap.appendChild(refsLine(actors, 'people.html'));
  }
  if (orgs.length) {
    wrap.appendChild(el('h3', { text: '관련 조직' }));
    wrap.appendChild(refsLine(orgs, 'organizations.html'));
  }
  return wrap;
}
function refsLine(refs, page) {
  const div = el('div', { class: 'tl-detail-refs' });
  refs.forEach((r, i) => {
    const sep = i ? document.createTextNode(', ') : null;
    if (sep) div.appendChild(sep);
    if (r.node_id && !r.ambiguous) {
      // 해소됨 → 앵커 링크
      div.appendChild(el('a', { href: `${page}#${r.node_id}`, text: r.name }));
    } else {
      // node_id null 또는 동명이호(ambiguous) → 평문(런타임 단정 차단)
      div.appendChild(el('span', { class: 'tl-ref-plain', text: r.name }));
    }
  });
  return div;
}

function renderSources(sources) {
  const ol = el('ol', { class: 'tl-source-list' });
  for (const s of sources) {
    const li = el('li', {});
    if (s.url) {
      li.appendChild(el('a', { href: s.url, text: s.title || s.url, target: '_blank', rel: 'noopener noreferrer' }));
    } else {
      li.appendChild(document.createTextNode(s.title || '(제목 미상)'));
    }
    if (s.locator) li.appendChild(document.createTextNode(`, ${s.locator}`));
    if (s.type) li.appendChild(el('span', { class: 'tl-source-type', text: ` [${s.type}]` }));
    ol.appendChild(li);
  }
  return ol;
}

/* ── 딥링크: #evt-id 하이라이트·스크롤, ?period=PN / ?tag / ?disputed 초기 필터 ── */
function applyInitialQuery() {
  const params = new URLSearchParams(location.search);
  const p = params.get('period');
  if (p && PERIODS[p]) { state.period = p; setChipActive('period', p); }
  const t = params.get('tag');
  if (t && TAG_ORDER.includes(t)) { state.tag = t; setChipActive('tag', t); }
  if (params.get('disputed') === '1') {
    state.disputedOnly = true;
    document.getElementById('tl-disputed-only').checked = true;
  }
}
function focusHashTarget() {
  const hash = location.hash.slice(1);
  if (!hash) return;
  const target = document.getElementById(hash);
  if (!target || !target.classList.contains('tl-event-card')) return;
  // 숨겨진 카드면 필터를 풀어 보이게(딥링크는 항상 도달 가능해야)
  if (target.hidden) {
    state.period = null; state.tag = null; state.disputedOnly = false;
    setChipActive('period', null); setChipActive('tag', null);
    document.getElementById('tl-disputed-only').checked = false;
    applyFilters();
  }
  target.classList.add('is-target');
  target.scrollIntoView({ behavior: prefersReducedMotion ? 'auto' : 'smooth', block: 'start' });
}

/* ── 이벤트 위임 + 컨트롤 배선 ─────────────────────────────────────────── */
function wireEvents() {
  // 목록 위임: 카드 제목/상세 버튼 클릭 → 패널 열기
  const list = document.getElementById('tl-list');
  list.addEventListener('click', (e) => {
    const opener = e.target.closest('[data-open]');
    if (opener) { openDetail(opener.dataset.open); return; }
  });

  // 패널 닫힘 → 원래 포커스 복귀(스킬 §1)
  const dlg = dialog();
  dlg.addEventListener('close', () => { if (lastFocused) lastFocused.focus(); });

  // 시기/태그 칩 위임
  document.querySelector('.tl-controls').addEventListener('click', (e) => {
    const chip = e.target.closest('.tl-chip');
    if (chip) {
      const kind = chip.dataset.filter;
      const value = chip.dataset.value || null;
      state[kind] = value;
      setChipActive(kind, value);
      applyFilters();
      return;
    }
    if (e.target.closest('#tl-reset')) {
      state.period = null; state.tag = null; state.disputedOnly = false;
      setChipActive('period', null); setChipActive('tag', null);
      document.getElementById('tl-disputed-only').checked = false;
      applyFilters();
    }
  });

  // disputed 토글
  document.getElementById('tl-disputed-only').addEventListener('change', (e) => {
    state.disputedOnly = e.target.checked;
    applyFilters();
  });

  // 해시 변경(타 페이지에서 #evt-id 진입) 대응
  window.addEventListener('hashchange', focusHashTarget);
}

/* ── 도입문(pages/timeline.json) 렌더 ─────────────────────────────────────
   §3.2·§3.6: 도입 내용은 sections[].blocks(이 페이지는 lead=[], 내용은 sections에).
   공통 page-render의 renderBlocks를 재사용한다(Policy 5 — 중복 구현 금지):
   renderInline이 [텍스트](href) md링크·**굵게**·내장 앵커를 처리하고
   [ref:ref-NNN] 마커는 원형 보존 → 이후 footnotes.renderFootnotes가 각주로 치환.
   페이지 헤더(h1)·필터 UI는 연표 고유 레이아웃(.tl-page-head)이라 renderPage 대신
   blocks만 .tl-lead 컨테이너에 렌더해 중복 제목/헤딩을 피한다.
*/
function renderLead(pageData) {
  if (!pageData) return;
  if (pageData.title) document.getElementById('tl-title').textContent = pageData.title;
  const leadEl = document.getElementById('tl-lead');
  // lead 필드(blocks 배열) + 각 섹션의 blocks를 순서대로 렌더. 슬롯은 도입문에 없음.
  if (Array.isArray(pageData.lead) && pageData.lead.length) {
    renderBlocks(leadEl, pageData.lead);
  }
  for (const sec of pageData.sections || []) {
    renderBlocks(leadEl, sec.blocks || []);
  }
}

/* footnotes 후처리 훅: 모듈이 준비되면 도입문 영역에만 적용.
   미준비 시 [ref:] 마커는 텍스트로 남되, 끊어진 각주처럼 빈 화면을 만들지 않는다. */
async function applyFootnotes(citations) {
  try {
    const mod = await import('./footnotes.js');
    const leadEl = document.getElementById('tl-lead');
    if (typeof mod.renderFootnotes === 'function') {
      mod.renderFootnotes(leadEl, citations);
      // 도입문 각주는 연표 앱 아래(페이지 하단)로 이동 — 본문 콘텐츠보다 위에 끼지 않게
      const fnSec = leadEl.querySelector('.footnotes');
      if (fnSec) (document.getElementById('app') || document.body).appendChild(fnSec);
    } else if (typeof mod.default === 'function') {
      mod.default(leadEl, citations);
    }
  } catch (err) {
    // footnotes.js 미존재/오류 — 도입문 마커는 텍스트로 남는다(빈 화면 아님).
    // 시그니처 확정 후 연결. console.warn으로 가시화.
    console.warn('[timeline] footnotes.js 미연결 — 도입문 각주는 마커 텍스트로 표시됩니다.', err);
  }
}

/* ── 부트 ─────────────────────────────────────────────────────────────── */
async function init() {
  // 공통 헤더·전역 내비·푸터 주입(layout.js 계약: mountLayout(currentKey)).
  // 데이터 로드보다 먼저 — 로드 실패 시에도 내비 가능한 셸 안에서 에러 UI가 보이게.
  try {
    mountLayout('timeline');
  } catch (err) {
    console.warn('[timeline] layout 주입 실패 — 본문은 계속 진행.', err);
  }

  let timeline, pageData;
  try {
    // 두 파일을 병렬 로드(§3.2: 데이터 + 도입문). 이름 충돌 주의(§5.6 — 전체 경로).
    [timeline, pageData] = await Promise.all([
      loadData('data/timeline.json'),
      loadData('data/pages/timeline.json').catch((e) => {
        // 도입문 로드 실패는 치명 아님 — 연표 본체는 살린다.
        console.warn('[timeline] 도입문(pages/timeline.json) 로드 실패 — 연표 본체만 표시.', e);
        return null;
      }),
    ]);
  } catch (err) {
    // 연표 데이터 자체 실패 → loader가 이미 에러 UI 렌더(§3.0). 중단.
    return;
  }

  allEvents = Array.isArray(timeline.events) ? timeline.events : [];
  if (!allEvents.length) {
    renderLoadError('data/timeline.json', new Error('사건 데이터가 비어 있습니다.'));
    return;
  }

  renderLead(pageData);
  buildFilterChips(allEvents);
  renderList(allEvents);
  wireEvents();
  applyInitialQuery();
  applyFilters();
  focusHashTarget();

  // 도입문 각주(있으면) 연결 — 별도 citations 로드 후 후처리.
  // footnotes 시그니처가 citations를 요구하면 여기서 전달.
  loadData('data/citations.json')
    .then((cit) => applyFootnotes(cit))
    .catch(() => applyFootnotes(null));
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
