/* gallery.js — 갤러리 페이지
   도입문(gallery-intro)은 page-render. 그 뒤에 images.json 80건을 그리드로 렌더한다.
   카드 = 이미지 + 사실 캡션 + 연대·시기·라이선스 메타 + credit + used_pages 역링크.
   앵커 gallery.html#{id}. 시기·유형 필터 칩(클라이언트 필터). */
import { loadAll } from './loader.js';
import { mountLayout } from './layout.js';
import { renderPage } from './page-render.js';
import { renderFootnotes } from './footnotes.js';

mountLayout('gallery');

const PERIODS = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8'];
const TYPE_LABELS = {
  portrait: '초상', group_photo: '단체사진', place: '장소', photo: '사진',
  document: '문서', newspaper: '신문', artifact: '유물', artwork: '작품',
};
const PAGE_LABELS = {
  home: '홈', life: '생애', timeline: '연표', map: '지도', organizations: '조직',
  philosophy: '사상', people: '인물', archives: '사료', gallery: '갤러리', references: '참고문헌',
};

function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]
  ));
}

function buildImageCard(img) {
  const fig = document.createElement('figure');
  fig.className = 'image-card';
  fig.id = img.id; // 무변형 앵커
  fig.setAttribute('data-period', img.period || '');
  fig.setAttribute('data-type', img.type || '');

  const image = document.createElement('img');
  image.src = img.src;
  image.alt = img.caption || img.title || '';
  image.loading = 'lazy';
  image.className = 'figure-img';
  image.style.filter = 'var(--img-filter)';
  fig.appendChild(image);

  const cap = document.createElement('figcaption');
  cap.className = 'figure-caption';

  const c = document.createElement('p');
  c.className = 'img-caption';
  c.textContent = img.caption || img.title || '';
  cap.appendChild(c);

  const meta = document.createElement('p');
  meta.className = 'img-meta';
  const bits = [];
  if (img.date) bits.push(esc(img.date));
  if (img.period) bits.push(esc(img.period));
  if (TYPE_LABELS[img.type]) bits.push(esc(TYPE_LABELS[img.type]));
  if (img.license) bits.push(esc(img.license));
  meta.innerHTML = bits.join(' · ');
  cap.appendChild(meta);

  if (img.credit) {
    const cr = document.createElement('p');
    cr.className = 'img-credit';
    cr.textContent = img.credit;
    cap.appendChild(cr);
  }

  // 사용 페이지 역링크(갤러리 자신 제외)
  const used = (img.used_pages || []).filter((p) => p !== 'gallery');
  if (used.length) {
    const bl = document.createElement('p');
    bl.className = 'img-backlinks';
    bl.innerHTML = '이 이미지가 쓰인 곳: ' + used
      .map((p) => `<a href="${p}.html">${esc(PAGE_LABELS[p] || p)}</a>`).join(', ');
    cap.appendChild(bl);
  }

  fig.appendChild(cap);
  return fig;
}

(async () => {
  const main = document.getElementById('app');
  try {
    const { page, images, citations } = await loadAll({
      page: 'data/pages/gallery.json',
      images: 'data/images.json',
      citations: 'data/citations.json',
    });
    renderPage(main, page, {});

    const all = images.images || [];

    // 필터 바(시기 + 유형)
    const section = document.createElement('section');
    section.className = 'page-section';
    section.id = 'gallery-grid';
    const filterBar = document.createElement('div');
    filterBar.className = 'filter-bar';
    filterBar.setAttribute('role', 'group');
    filterBar.setAttribute('aria-label', '갤러리 필터');

    const presentPeriods = PERIODS.filter((p) => all.some((i) => i.period === p));
    const presentTypes = Object.keys(TYPE_LABELS).filter((t) => all.some((i) => i.type === t));

    const chip = (label, kind, val) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'filter-chip' + (val === '' ? ' is-active' : '');
      b.textContent = label;
      b.setAttribute('data-filter-kind', kind);
      b.setAttribute('data-filter-val', val);
      b.setAttribute('aria-pressed', val === '' ? 'true' : 'false');
      return b;
    };
    filterBar.appendChild(chip('전체', 'period', ''));
    presentPeriods.forEach((p) => filterBar.appendChild(chip(p, 'period', p)));
    presentTypes.forEach((t) => filterBar.appendChild(chip(TYPE_LABELS[t], 'type', t)));
    section.appendChild(filterBar);

    const grid = document.createElement('div');
    grid.className = 'gallery-grid';
    all.forEach((img) => grid.appendChild(buildImageCard(img)));
    section.appendChild(grid);
    main.appendChild(section);

    // 클라이언트 필터(시기·유형 각 단일 선택, OR 아님 — period와 type 동시 AND)
    let activePeriod = '', activeType = '';
    filterBar.addEventListener('click', (ev) => {
      const btn = ev.target.closest('.filter-chip');
      if (!btn) return;
      const kind = btn.getAttribute('data-filter-kind');
      const val = btn.getAttribute('data-filter-val');
      if (kind === 'period') activePeriod = val;
      else activeType = val;
      // 같은 kind 칩 active 토글
      filterBar.querySelectorAll(`[data-filter-kind="${kind}"]`).forEach((b) => {
        const on = b.getAttribute('data-filter-val') === val;
        b.classList.toggle('is-active', on);
        b.setAttribute('aria-pressed', String(on));
      });
      let shown = 0;
      grid.querySelectorAll('.image-card').forEach((card) => {
        const okP = !activePeriod || card.getAttribute('data-period') === activePeriod;
        const okT = !activeType || card.getAttribute('data-type') === activeType;
        const show = okP && okT;
        card.style.display = show ? '' : 'none';
        if (show) shown++;
      });
      let empty = section.querySelector('.empty-state');
      if (shown === 0) {
        if (!empty) {
          empty = document.createElement('p');
          empty.className = 'empty-state';
          empty.textContent = '해당 조건의 이미지가 없습니다.';
          section.appendChild(empty);
        }
      } else if (empty) {
        empty.remove();
      }
    });

    renderFootnotes(main, citations);
  } catch (err) { /* renderLoadError가 이미 렌더 */ }
})();
