/* organizations.js — 조직 페이지 (일반 페이지 패턴 + org 앵커 보장) */
import { loadAll } from './loader.js';
import { mountLayout } from './layout.js';
import { renderPage, makeSlotResolver } from './page-render.js';
import { renderFootnotes } from './footnotes.js';

mountLayout('organizations');

(async () => {
  const main = document.getElementById('app');
  try {
    const { page, images, citations, network } = await loadAll({
      page: 'data/pages/organizations.json',
      images: 'data/images.json',
      citations: 'data/citations.json',
      network: 'data/network.json',
    });
    renderPage(main, page, { slotResolver: makeSlotResolver(images) });

    // 교차링크 앵커 보장(§5.2): 다른 페이지가 organizations.html#org-NNN 로 들어올 수 있다.
    // 본문 서사에 인라인 앵커가 없는 조직도 앵커가 존재해야 끊어진 링크가 0.
    const orgNodes = (network.nodes || []).filter((n) => n.kind === 'org');
    const missing = orgNodes.filter((n) => !document.getElementById(n.id));
    if (missing.length) {
      const host = document.createElement('div');
      host.className = 'nw-anchor-host';
      missing.forEach((n) => {
        const a = document.createElement('span');
        a.id = n.id;
        a.className = 'nw-anchor';
        host.appendChild(a);
      });
      main.appendChild(host);
    }

    renderFootnotes(main, citations);
  } catch (err) { /* renderLoadError가 이미 렌더 */ }
})();
