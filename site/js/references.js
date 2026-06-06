/* references.js — 참고문헌 페이지
   본문(방법론·등급·콜로폰)은 page-render. #citations 섹션에는 citations.json sources를
   유형별로 그룹해 id={source_id} 앵커와 함께 일람으로 렌더한다(전 페이지 각주의 종착점). */
import { loadAll } from './loader.js';
import { mountLayout } from './layout.js';
import { renderPage } from './page-render.js';
import { renderFootnotes } from './footnotes.js';

mountLayout('references');

// 출처 유형 → 한글 그룹명·정렬 순서
const TYPE_GROUPS = [
  ['primary', '1차 사료'],
  ['academic', '학술 논저'],
  ['institutional', '기관 DB·사전'],
  ['encyclopedia', '백과·사전'],
  ['newspaper', '신문·잡지'],
  ['web', '웹 자료'],
];

function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]
  ));
}

function buildSourceItem(src) {
  const li = document.createElement('li');
  li.id = src.id; // 무변형 앵커 — references.html#{source_id}
  const bits = [];
  if (src.author) bits.push(esc(src.author));
  if (src.title) bits.push(`「${esc(src.title)}」`);
  if (src.publisher) bits.push(esc(src.publisher));
  if (src.year) bits.push(esc(String(src.year)));
  let html = `<span class="src-cite">${bits.join(', ')}</span>`;
  if (src.url) {
    html += ` <a class="footnote-url" href="${esc(src.url)}" target="_blank" rel="noopener noreferrer">원문 링크</a>`;
  }
  html += ` <span class="src-type mono-wrap">${esc(src.id)}</span>`;
  li.innerHTML = html;
  return li;
}

function renderCitationList(citationsSection, sources) {
  // 그룹핑
  const byType = new Map();
  sources.forEach((s) => {
    const t = s.type || 'web';
    if (!byType.has(t)) byType.set(t, []);
    byType.get(t).push(s);
  });
  // 그룹별 렌더(정의된 순서 → 나머지)
  const seen = new Set();
  const order = TYPE_GROUPS.filter(([t]) => byType.has(t));
  [...byType.keys()].forEach((t) => {
    if (!TYPE_GROUPS.some(([tt]) => tt === t)) order.push([t, t]);
  });
  order.forEach(([type, label]) => {
    if (seen.has(type)) return;
    seen.add(type);
    const list = byType.get(type);
    if (!list || !list.length) return;
    const group = document.createElement('div');
    group.className = 'source-group';
    const h = document.createElement('h3');
    h.className = 'section-subheading';
    h.textContent = `${label} (${list.length})`;
    group.appendChild(h);
    const ol = document.createElement('ul');
    ol.className = 'source-list';
    list.sort((a, b) => String(a.id).localeCompare(String(b.id)));
    list.forEach((s) => ol.appendChild(buildSourceItem(s)));
    group.appendChild(ol);
    citationsSection.appendChild(group);
  });
}

(async () => {
  const main = document.getElementById('app');
  try {
    const { page, citations } = await loadAll({
      page: 'data/pages/references.json',
      citations: 'data/citations.json',
    });
    renderPage(main, page, {
      // #citations 섹션 렌더 직후 sources 일람을 주입
      sectionHook: (sectionEl, section) => {
        if (section.id === 'citations') {
          renderCitationList(sectionEl, citations.sources || []);
        }
      },
    });
    renderFootnotes(main, citations);
  } catch (err) { /* renderLoadError가 이미 렌더 */ }
})();
