/* archives.js — 사료 페이지
   본문(도입·비판·미확인·채택안한전승·공백)은 page-render. #catalog 섹션에 archives.json
   카탈로그 47건을 유형별로 그룹해 카드로 주입한다. 앵커=src-pri-NNN 무변형.
   related_event_ids는 이미 생존 id로 해소·필터됨(D-24) — 추가 해소 불요, 그대로 timeline 링크. */
import { loadAll } from './loader.js';
import { mountLayout } from './layout.js';
import { renderPage, makeSlotResolver } from './page-render.js';
import { renderFootnotes } from './footnotes.js';

mountLayout('archives');

const TYPE_LABELS = {
  diary: '일기', letter: '서한', speech: '연설문', newspaper: '신문',
  interrogation: '신문조서', verdict: '판결문', org_record: '단체 기록', etc: '기타',
};
const LOC = {
  confirmed: { cls: 'is-loc-confirmed', label: '소재 확인' },
  cited_only: { cls: 'is-loc-cited', label: '인용만 확인' },
  unlocated: { cls: 'is-loc-unlocated', label: '소재 미확인' },
};

function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]
  ));
}

function buildCard(item) {
  const card = document.createElement('article');
  card.className = 'archive-card';
  card.id = item.id; // 무변형 앵커

  const head = document.createElement('div');
  head.className = 'archive-head';
  head.innerHTML = `<h3 class="archive-title">${esc(item.title)}</h3>`;
  const loc = LOC[item.location_status];
  if (loc) {
    head.innerHTML += `<span class="loc-badge ${loc.cls}">${loc.label}</span>`;
  }
  card.appendChild(head);

  // 메타 정의 목록
  const dl = document.createElement('dl');
  dl.className = 'archive-meta';
  const meta = [];
  if (item.type) meta.push(['유형', TYPE_LABELS[item.type] || item.type]);
  if (item.author) meta.push(['작성', item.author]);
  if (item.date_created) meta.push(['시기', item.date_created]);
  if (item.holder) meta.push(['소장', item.holder]);
  dl.innerHTML = meta.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('');
  card.appendChild(dl);

  if (item.access_url) {
    const a = document.createElement('p');
    a.className = 'archive-meta';
    a.innerHTML = `<a class="mono-wrap" href="${esc(item.access_url)}" target="_blank" rel="noopener noreferrer">소장처 링크</a>`;
    card.appendChild(a);
  }

  // 전사·현대어(있으면)
  if (item.transcription) {
    const p = document.createElement('div');
    p.className = 'criticism-block';
    p.innerHTML = `<p class="criticism-label">전사(轉寫)</p><p>${esc(item.transcription)}</p>`;
    card.appendChild(p);
  }
  if (item.modern_translation) {
    const p = document.createElement('div');
    p.className = 'criticism-block';
    p.innerHTML = `<p class="criticism-label">현대어 풀이</p><p>${esc(item.modern_translation)}</p>`;
    card.appendChild(p);
  }

  // 사료 비판(외적·내적)
  if (item.criticism) {
    if (item.criticism.external) {
      const b = document.createElement('div');
      b.className = 'criticism-block';
      b.innerHTML = `<p class="criticism-label">외적 비판</p><p>${esc(item.criticism.external)}</p>`;
      card.appendChild(b);
    }
    if (item.criticism.internal) {
      const b = document.createElement('div');
      b.className = 'criticism-block';
      b.innerHTML = `<p class="criticism-label">내적 비판</p><p>${esc(item.criticism.internal)}</p>`;
      card.appendChild(b);
    }
  }

  // 근거 사건(이미 생존 id로 해소·필터됨)
  const evs = item.related_event_ids || [];
  const ep = document.createElement('p');
  ep.className = 'archive-meta';
  if (evs.length) {
    ep.innerHTML = '근거 사건: ' + evs
      .map((ev) => `<a href="timeline.html#${esc(ev)}">${esc(ev)}</a>`).join(', ');
  } else {
    ep.innerHTML = '<span class="src-type">근거 사건 링크 없음</span>';
  }
  card.appendChild(ep);

  if (item.notes) {
    const n = document.createElement('p');
    n.className = 'archive-meta';
    n.textContent = item.notes;
    card.appendChild(n);
  }
  return card;
}

function renderCatalog(sectionEl, catalog) {
  // 유형별 그룹(정의 순서)
  const order = Object.keys(TYPE_LABELS);
  const byType = new Map();
  catalog.forEach((c) => {
    const t = c.type || 'etc';
    if (!byType.has(t)) byType.set(t, []);
    byType.get(t).push(c);
  });
  const seen = new Set();
  [...order, ...byType.keys()].forEach((type) => {
    if (seen.has(type) || !byType.has(type)) return;
    seen.add(type);
    const list = byType.get(type);
    const group = document.createElement('div');
    group.className = 'archive-type-group';
    const h = document.createElement('h3');
    h.className = 'section-subheading';
    h.textContent = `${TYPE_LABELS[type] || type} (${list.length})`;
    group.appendChild(h);
    list.forEach((c) => group.appendChild(buildCard(c)));
    sectionEl.appendChild(group);
  });
}

(async () => {
  const main = document.getElementById('app');
  try {
    const { page, archives, images, citations } = await loadAll({
      page: 'data/pages/archives.json',
      archives: 'data/archives.json',
      images: 'data/images.json',
      citations: 'data/citations.json',
    });
    renderPage(main, page, {
      slotResolver: makeSlotResolver(images),
      sectionHook: (sectionEl, section) => {
        if (section.id === 'catalog') renderCatalog(sectionEl, archives.catalog || []);
      },
    });
    renderFootnotes(main, citations);
  } catch (err) { /* renderLoadError가 이미 렌더 */ }
})();
