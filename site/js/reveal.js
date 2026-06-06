/* reveal.js — 스크롤 리빌 공유 모듈 (v2 §10.2). frontend-developer 소유.
   IO로 .is-revealed 토글. JS만 .is-pre-reveal(opacity:0;translateY) 부여 후 관찰 →
   no-JS면 그대로 보임(CSS 기본 숨김 금지). reduced-motion은 tokens.css가 --dur-reveal·
   --reveal-shift를 0으로 중화 → 즉시 최종 상태. timeline/map은 layout.js가 key로 제외.
   REV-1 안전망: lazy 이미지 뒤늦은 로드 리플로우 × IO once 어긋남으로 카드가 opacity:0에
   영구 고정되던 게이트 결함 수정 — ① 양수 bottom rootMargin 선반응 ② img load·스크롤 시
   in-view 스윕 ③ 6초 후 잔여 강제 해제(가시성 > 연출, 영구 숨김 0 보장). */
const REVEAL_SELECTOR = '.page-section, .card-grid > *, .gallery-grid > *, .archive-card, .quote-block';

let io = null;
const seen = new WeakSet();
const armed = new Set(); // 미리빌 카드(스윕·안전망 대상)

function reveal(el) { el.classList.add('is-revealed'); armed.delete(el); }

function ensureObserver() {
  if (io) return io;
  io = new IntersectionObserver((entries, obs) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      reveal(entry.target);
      obs.unobserve(entry.target);
    });
  }, { rootMargin: '0px 0px 64px 0px', threshold: 0 }); // 진입 직전 선반응(리플로우 레이스 완화)
  return io;
}

// 그룹 자식 순차 지연(토큰 --reveal-stagger × n, 6개까지). 하드코딩 ms 금지.
function staggerDelay(el) {
  const parent = el.parentElement;
  if (!parent || !parent.matches('.card-grid, .gallery-grid')) return;
  const idx = Array.prototype.indexOf.call(parent.children, el);
  if (idx > 0) el.style.transitionDelay = `calc(var(--reveal-stagger) * ${Math.min(idx, 6)})`;
}

function arm(el) {
  if (seen.has(el)) return;
  seen.add(el);
  el.classList.add('is-pre-reveal'); // JS만 부여 — no-JS 폴백 안전
  staggerDelay(el);
  armed.add(el);
  ensureObserver().observe(el);
  // REV-1 ②: 카드 내 이미지 뒤늦은 로드(리플로우) 시 교차 재평가.
  el.querySelectorAll('img').forEach((img) => {
    if (img.complete) return;
    img.addEventListener('load', sweepInView, { once: true, passive: true });
    img.addEventListener('error', sweepInView, { once: true, passive: true });
  });
}

// top < vh+64 단조 조건 — 아래에서 한 번 진입하면 빠른 스크롤로 지나쳐도 리빌 유지.
function sweepInView() {
  if (!armed.size) return;
  const vh = window.innerHeight || document.documentElement.clientHeight;
  armed.forEach((el) => {
    if (el.getBoundingClientRect().top < vh + 64) { reveal(el); if (io) io.unobserve(el); }
  });
}

function scan(root) { root.querySelectorAll(REVEAL_SELECTOR).forEach(arm); }

export function initReveal(root) {
  if (!('IntersectionObserver' in window)) return; // 폴백: 대상 그대로 보임
  const host = root || document.getElementById('app') || document.body;
  if (!host) return;
  scan(host);
  const mo = new MutationObserver((muts) => {
    for (const m of muts) {
      m.addedNodes.forEach((node) => {
        if (node.nodeType !== 1) return;
        if (node.matches && node.matches(REVEAL_SELECTOR)) arm(node);
        if (node.querySelectorAll) scan(node);
      });
    }
  });
  mo.observe(host, { childList: true, subtree: true });

  // REV-1 ②: 스크롤/리사이즈 시 in-view 스윕(passive·rAF 디바운스). IO는 유지(연출).
  let ticking = false;
  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => { sweepInView(); ticking = false; });
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
  [400, 1200, 3000].forEach((t) => setTimeout(sweepInView, t)); // lazy 안정화 구간 보정

  // REV-1 ③ 안전망: 6초 후 잔여 미리빌 전부 강제 해제(영구 숨김 0). 이후 리스너 정리.
  setTimeout(() => {
    mo.disconnect();
    armed.forEach((el) => { el.classList.add('is-revealed'); if (io) io.unobserve(el); });
    armed.clear();
    window.removeEventListener('scroll', onScroll);
    window.removeEventListener('resize', onScroll);
  }, 6000);
}
