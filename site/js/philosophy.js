/* philosophy.js — 사상 페이지 (일반 페이지 패턴, 어록 검증표는 table 블록으로 렌더됨) */
import { loadAll } from './loader.js';
import { mountLayout } from './layout.js';
import { renderPage, makeSlotResolver } from './page-render.js';
import { renderFootnotes } from './footnotes.js';

mountLayout('philosophy');

(async () => {
  const main = document.getElementById('app');
  try {
    const { page, images, citations } = await loadAll({
      page: 'data/pages/philosophy.json',
      images: 'data/images.json',
      citations: 'data/citations.json',
    });
    renderPage(main, page, { slotResolver: makeSlotResolver(images) });
    renderFootnotes(main, citations);
  } catch (err) { /* renderLoadError가 이미 렌더 */ }
})();
