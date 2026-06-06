/* ==========================================================================
   loader.js — 공통 데이터 로더 (공유 모듈)
   --------------------------------------------------------------------------
   계약: architecture.md §3.0
     export async function loadData(path) -> Promise<object|array>
       성공: 파싱된 JSON 반환
       실패(네트워크·HTTP!=200·JSON 파싱 오류): renderLoadError 호출 후 throw
     export function renderLoadError(path, err) -> void
       사용자에게 보이는 에러 UI 렌더 — 빈 화면 금지(§5.1)

   소유: frontend-developer. 시그니처 변경 시 전 소비자(timeline·map·전 페이지) 사전 고지.
   경로는 페이지 기준 상대 경로(data/...). 절대 경로 금지(서브디렉토리 호스팅 호환, D-11).
   ========================================================================== */

/**
 * JSON 데이터를 fetch로 로드해 파싱한다.
 * 모든 데이터 로드는 이 함수를 경유한다(직접 fetch 금지 — 에러 UI 일관성·QA 추적성).
 * @param {string} path  페이지 기준 상대 경로 (예: "data/timeline.json")
 * @returns {Promise<object|array>}  파싱된 JSON
 * @throws  실패 시 renderLoadError 호출 후 throw (빈 객체 반환하지 않음 — null 정책 §3.0)
 */
export async function loadData(path) {
  let res;
  try {
    res = await fetch(path, { cache: 'no-cache' });
  } catch (err) {
    // 네트워크 오류 — file:// CORS 차단 포함(§5.1)
    renderLoadError(path, err);
    throw err;
  }
  if (!res.ok) {
    const err = new Error(`HTTP ${res.status} ${res.statusText} — ${path}`);
    renderLoadError(path, err);
    throw err;
  }
  try {
    return await res.json();
  } catch (err) {
    renderLoadError(path, err);
    throw err;
  }
}

/**
 * 여러 데이터 파일을 병렬 로드한다. 하나라도 실패하면 첫 실패의 에러 UI가 렌더되고 throw.
 * @param {Record<string,string>} pathMap  { key: path } 형태
 * @returns {Promise<Record<string,object|array>>}  { key: data }
 */
export async function loadAll(pathMap) {
  const keys = Object.keys(pathMap);
  const results = await Promise.all(keys.map((k) => loadData(pathMap[k])));
  const out = {};
  keys.forEach((k, i) => { out[k] = results[i]; });
  return out;
}

/**
 * 데이터 로드 실패 시 사용자에게 보이는 에러 UI를 렌더한다.
 * 타깃: [data-load-error] 요소 → 없으면 #app → 없으면 <main> → 없으면 body 상단.
 * 빈 화면 금지(§5.1) — 실패 경로 + 로컬 서버 안내를 노출한다.
 * @param {string} path
 * @param {Error}  err
 */
export function renderLoadError(path, err) {
  const target =
    document.querySelector('[data-load-error]') ||
    document.getElementById('app') ||
    document.querySelector('main') ||
    document.body;

  const box = document.createElement('div');
  box.className = 'load-error';
  box.setAttribute('role', 'alert');
  box.innerHTML = `
    <h2 class="load-error-title">데이터를 불러오지 못했습니다</h2>
    <p class="load-error-path"><code></code></p>
    <p class="load-error-hint">
      이 페이지는 로컬 서버에서 열어야 합니다. 파일을 더블클릭해
      <code>file://</code>로 열면 브라우저가 데이터 요청을 차단합니다.<br>
      터미널에서 다음을 실행한 뒤
      <code>http://localhost:8000</code>으로 여세요:
    </p>
    <pre class="load-error-cmd">cd site &amp;&amp; python3 -m http.server 8000</pre>
    <p class="load-error-detail"></p>
  `;
  // 텍스트는 안전하게 textContent로 주입(경로·에러 메시지의 임의 마크업 차단)
  box.querySelector('.load-error-path code').textContent = path;
  box.querySelector('.load-error-detail').textContent = `오류: ${err && err.message ? err.message : err}`;

  // 타깃을 비우지 않고 맨 앞에 알림을 둔다(다른 콘텐츠가 이미 있을 수 있음)
  target.prepend(box);
  // 콘솔에도 남겨 QA가 추적(§5.5 조용히 삼키지 않음)
  console.error(`[loadData] 데이터 로드 실패: ${path}`, err);
}
