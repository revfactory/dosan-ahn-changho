/* ==========================================================================
   footnotes.js — [ref:ref-NNN] 각주 렌더 (전 페이지 공유 모듈, §3.4 / D-06)
   --------------------------------------------------------------------------
   렌더 경로(§3.4):
     본문 [ref:ref-NNN] → refs[]에서 id==ref-NNN 조회 → source_id 획득
       → sources[]에서 해당 id 조회 → 각주 번호 + references.html#{source_id} 앵커
   규약:
     1. 페이지 본문 렌더 후 텍스트 노드의 [ref:ref-NNN]을 스캔.
     2. 위첨자 각주 번호 <sup><a href="references.html#{source_id}">N</a></sup>로 치환.
        페이지 내 등장 순서로 번호 부여.
     3. 같은 ref-NNN 재등장 → 같은 번호 재사용(중복 부여 금지).
     4. 페이지 하단에 각주 목록 섹션 생성(번호 → 서지 약식 + references 앵커).
   null/누락:
     ref-NNN이 refs[]에 없음 / source_id가 sources[]에 없음 → 끊어진 각주.
       빈 화면 금지 — [ref:ref-NNN ⚠]로 가시화 + console.warn(§5.5). qa가 검출.
   소유: frontend-developer. 시그니처 변경 시 전 소비자 사전 고지.
   ========================================================================== */

const MARKER_RE = /\[ref:(ref-\d+)\]/g;

/**
 * citations.json을 빠른 조회용 인덱스로 변환.
 * @param {{refs:Array, sources:Array}} citations
 * @returns {{refIndex:Map, sourceIndex:Map}}
 */
export function buildCitationIndex(citations) {
  const refIndex = new Map();
  const sourceIndex = new Map();
  (citations.refs || []).forEach((r) => refIndex.set(r.id, r));
  (citations.sources || []).forEach((s) => sourceIndex.set(s.id, s));
  return { refIndex, sourceIndex };
}

/**
 * 출처 객체를 각주 목록용 약식 서지 문자열로 만든다.
 * @param {object} src  sources[] 항목
 * @param {object|null} ref  refs[] 항목(page_or_locator 보유 가능)
 */
function formatSource(src, ref) {
  const parts = [];
  if (src.author) parts.push(src.author);
  if (src.title) parts.push(`「${src.title}」`);
  if (src.publisher) parts.push(src.publisher);
  if (src.year) parts.push(String(src.year));
  let bib = parts.join(', ');
  const loc = ref && ref.page_or_locator;
  if (loc) bib += ` (${loc})`;
  return bib || src.id;
}

/**
 * 한 루트 요소 안의 [ref:ref-NNN] 마커를 각주 번호로 치환하고,
 * 루트 끝에 각주 목록 섹션을 덧붙인다.
 *
 * @param {HTMLElement} root  본문이 이미 렌더된 컨테이너
 * @param {{refs:Array, sources:Array}} citations
 * @param {object} [opts]
 * @param {string} [opts.refBase="references.html"]  각주 앵커가 가리킬 페이지
 * @returns {{count:number, broken:string[]}}  부여된 각주 수, 끊어진 ref-id 목록
 */
export function renderFootnotes(root, citations, opts = {}) {
  const refBase = opts.refBase || 'references.html';
  const { refIndex, sourceIndex } = buildCitationIndex(citations);

  // ref-NNN → 페이지 내 각주 번호(중복 재사용)
  const numberOf = new Map();
  // 각주 번호 → { refId, sourceId, bib } (목록 렌더용)
  const entries = [];
  const broken = [];

  // 텍스트 노드만 순회(이미 생성된 <a>·<sup> 내부는 마커가 없으므로 안전)
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      return MARKER_RE.test(node.nodeValue)
        ? NodeFilter.FILTER_ACCEPT
        : NodeFilter.FILTER_REJECT;
    },
  });
  // TreeWalker는 라이브 컬렉션이라 치환 중 DOM을 바꾸면 위험 → 먼저 수집
  const textNodes = [];
  let n;
  while ((n = walker.nextNode())) textNodes.push(n);

  for (const textNode of textNodes) {
    const text = textNode.nodeValue;
    MARKER_RE.lastIndex = 0;
    if (!MARKER_RE.test(text)) continue;
    MARKER_RE.lastIndex = 0;

    const frag = document.createDocumentFragment();
    let lastIndex = 0;
    let m;
    while ((m = MARKER_RE.exec(text)) !== null) {
      const refId = m[1];
      // 마커 앞 평문
      if (m.index > lastIndex) {
        frag.appendChild(document.createTextNode(text.slice(lastIndex, m.index)));
      }
      lastIndex = m.index + m[0].length;

      const ref = refIndex.get(refId);
      const source = ref ? sourceIndex.get(ref.source_id) : null;

      if (!ref || !source) {
        // 끊어진 각주 — 가시화 + warn(빈 화면 금지, §5.5)
        broken.push(refId);
        const warn = document.createElement('sup');
        warn.className = 'footnote-broken';
        warn.title = !ref
          ? `끊어진 각주: ${refId} 가 인용 목록에 없습니다`
          : `끊어진 출처: ${ref.source_id} 가 출처 목록에 없습니다`;
        warn.textContent = `[ref:${refId} ⚠]`;
        frag.appendChild(warn);
        console.warn(
          `[footnotes] 끊어진 각주: ${refId}` +
          (ref ? ` → source_id ${ref.source_id} 미존재` : ' (refs[]에 없음)')
        );
        continue;
      }

      // 정상 각주 — 번호 부여(중복 재사용)
      let num = numberOf.get(refId);
      if (num === undefined) {
        num = entries.length + 1;
        numberOf.set(refId, num);
        entries.push({
          num,
          refId,
          sourceId: source.id,
          bib: formatSource(source, ref),
          url: source.url || null,
        });
      }
      const sup = document.createElement('sup');
      sup.className = 'footnote-ref';
      sup.id = `fnref-${num}`;
      const a = document.createElement('a');
      a.href = `${refBase}#${source.id}`;
      a.setAttribute('aria-label', `각주 ${num}, 출처 보기`);
      a.textContent = String(num);
      sup.appendChild(a);
      frag.appendChild(sup);
    }
    // 마커 뒤 남은 평문
    if (lastIndex < text.length) {
      frag.appendChild(document.createTextNode(text.slice(lastIndex)));
    }
    textNode.parentNode.replaceChild(frag, textNode);
  }

  if (entries.length > 0) {
    root.appendChild(buildFootnoteList(entries, refBase));
  }

  return { count: entries.length, broken };
}

function buildFootnoteList(entries, refBase) {
  const section = document.createElement('section');
  section.className = 'footnotes';
  section.setAttribute('aria-label', '각주');
  const h = document.createElement('h2');
  h.className = 'footnotes-title';
  h.textContent = '각주';
  section.appendChild(h);

  const ol = document.createElement('ol');
  ol.className = 'footnotes-list';
  for (const e of entries) {
    const li = document.createElement('li');
    li.id = `fn-${e.num}`;
    li.className = 'footnote-item';

    const bibLink = document.createElement('a');
    bibLink.href = `${refBase}#${e.sourceId}`;
    bibLink.className = 'footnote-bib';
    bibLink.textContent = e.bib;
    li.appendChild(bibLink);

    if (e.url) {
      const sep = document.createTextNode(' ');
      li.appendChild(sep);
      const ext = document.createElement('a');
      ext.href = e.url;
      ext.className = 'footnote-url';
      ext.target = '_blank';
      ext.rel = 'noopener noreferrer';
      ext.textContent = '원문 링크';
      li.appendChild(ext);
    }

    // 본문으로 되돌아가는 링크(접근성)
    const back = document.createElement('a');
    back.href = `#fnref-${e.num}`;
    back.className = 'footnote-back';
    back.setAttribute('aria-label', `각주 ${e.num} 인용 위치로 돌아가기`);
    back.textContent = '↩';
    li.appendChild(document.createTextNode(' '));
    li.appendChild(back);

    ol.appendChild(li);
  }
  section.appendChild(ol);
  return section;
}
