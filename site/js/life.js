/* life.js — 생애 페이지 (일반 페이지 패턴: page-render + footnotes + slots) */
import { loadAll } from './loader.js';
import { mountLayout } from './layout.js';
import { renderPage, makeSlotResolver } from './page-render.js';
import { renderFootnotes } from './footnotes.js';

mountLayout('life');

(async () => {
  const main = document.getElementById('app');
  try {
    const { page, images, citations } = await loadAll({
      page: 'data/pages/life.json',
      images: 'data/images.json',
      citations: 'data/citations.json',
    });
    renderPage(main, page, { slotResolver: makeSlotResolver(images) });
    renderFootnotes(main, citations);
  } catch (err) {
    // 에러 UI는 loader.renderLoadError가 이미 렌더함(빈 화면 금지)
  }
})();
