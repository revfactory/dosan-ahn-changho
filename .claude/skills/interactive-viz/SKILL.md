---
name: interactive-viz
description: 인터랙티브 연표와 Leaflet 활동 지도의 구현 패턴 — 데이터 바인딩, disputed/추정 날짜 표시, 시기 필터·슬라이더, 경로 폴리라인, 성능(이벤트 위임·지연 렌더), 비JS 폴백, motion-reduce, 키보드 접근성을 정의하는 스킬. timeline-developer(25)가 timeline.html/js를, map-developer(26)가 map.html/js를 구현할 때 반드시 사용하고, frontend-developer(24)도 페이지 내 소형 시각화 시 참조하라. "연표 수정", "지도 보완", "인터랙션 개선", "필터 다시", "성능 보완", "폴백 추가" 같은 후속 요청 시에도 이 스킬의 패턴과 폴백 규칙을 기준으로 작업하라.
---

# 인터랙티브 시각화 (interactive-viz)

연표와 지도는 이 사이트에서 데이터(timeline.json, network.json)가 직접 화면이 되는 컴포넌트다. 시각화의 원칙은 하나다 — **인터랙션은 사료를 더 잘 보여주기 위한 수단이지, 그 자체가 볼거리가 아니다.** 모든 패턴은 (1) 데이터 스키마를 소비만 하고 변형하지 않으며 (2) JS가 없거나 모션을 줄인 환경에서도 내용 접근이 가능하고 (3) 사건 수가 늘어도 성능이 유지되도록 설계한다.

## 1. 연표 컴포넌트 패턴

### 기본 구조: 세로 스크롤 + 시기 점프 내비

가로 스크롤 연표는 모바일에서 조작이 어렵고 스크린리더 선형 탐색과 충돌한다. **세로 스크롤을 기본**으로 하고, 상단에 고정된 시기 점프 내비(생애 시기 구분: 초년기/미주/신민회/임정/흥사단·말년 등)를 둬라.

```js
// 데이터 바인딩 — timeline.json을 소비만 한다
const { events } = await loadData('data/timeline.json');
// 스키마 변형 금지: 필요한 가공(정렬·그룹핑)은 사본에, 원본 구조는 불변
const sorted = [...events].sort((a, b) => a.date.start.localeCompare(b.date.start));
```

- **스키마는 소비만.** 필드 추가·이름 변경이 필요하면 data-engineer에 요청하라. 컴포넌트 안에서 데이터를 "고치면" 그 순간 데이터 단일 진실이 깨지고 content-qa의 대조가 무의미해진다.
- **렌더링은 데이터 주도로.** 사건 카드를 HTML에 하드코딩하지 말고 전부 JSON에서 생성하라.

### 불확실성의 정직한 표시

역사 데이터의 불확실성은 시각화에서 숨기기 쉽고, 숨기는 순간 사이트가 거짓을 말하게 된다.

- `date.precision`이 `month`/`year`/`range`인 사건은 날짜를 그 정밀도대로 표기("1907년", "1913년 5월", "1910년 봄~여름"). 임의로 1일로 환원해 표시하지 마라.
- `calendar: lunar`인 날짜는 "(음력)" 병기.
- `disputed: true` 사건은 시각 마커(점선 테두리) + 텍스트 라벨("기록 상충")을 함께 — 색이나 아이콘만으로 구분하면 색각 이상·스크린리더 사용자가 알 수 없다.
- `confidence: C` 사건이 표시될 경우 "전기류 기록" 등 등급 표시를 동반하라.

### 필터

시기 필터와 카테고리(tags) 필터는 **데이터를 다시 그리지 않고** DOM 노드의 표시/숨김으로 처리하라(60+개 수준에서는 이것이 가장 단순하고 충분히 빠르다). 필터 상태는 URL 해시에 반영해 특정 필터 화면을 링크로 공유할 수 있게 하라. 필터 결과 0건일 때는 빈 화면이 아니라 "해당 사건 없음" 메시지를 표시하라.

### 사건 상세 패널

카드 클릭/Enter 시 상세 패널(detail, 출처 목록, 관련 인물 링크)을 연다. 패널은 네이티브 `<dialog>`를 우선 사용하라 — 포커스 트랩·Esc 닫기·배경 비활성화를 브라우저가 무료로 제공하므로, 커스텀 모달로 같은 것을 다시 구현하는 것은 접근성 부채를 사는 일이다.

```js
const dialog = document.getElementById('event-detail');
let lastFocused = null;

function openDetail(eventId) {
  lastFocused = document.activeElement;        // 복귀 지점 기억
  renderDetail(dialog, findEvent(eventId));    // 지연 렌더 — 열릴 때 생성
  dialog.showModal();                          // 포커스 이동·Esc·트랩 자동
}
dialog.addEventListener('close', () => lastFocused?.focus()); // 원래 카드로 복귀
```

상세 패널의 출처 목록은 citations.json의 id를 참고문헌 페이지 앵커로 링크하라 — 연표에서 출처까지의 동선이 끊기면 "출처 있음" 표시가 장식이 된다.

## 2. 지도 패턴 (Leaflet)

```js
const map = L.map('map', { scrollWheelZoom: false }); // 페이지 스크롤 충돌 방지
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors', // OSM 정책상 의무
  maxZoom: 18,
}).addTo(map);
```

- **타일은 OSM 무료 정책 준수:** attribution 의무 표기, 과도한 요청 금지. 타일 로드 실패 시(오프라인·차단) 지도 영역에 거점 목록 텍스트를 폴백으로 표시하라.
- **좌표는 timeline.json의 place 데이터만 사용.** 임의 좌표를 JS에 하드코딩하면 데이터와 화면이 분기된다. 좌표가 필요한데 없으면 data-engineer 경유로 추가하라.
- **마커는 거점 단위로.** 거점 수십 개 수준이므로 클러스터링 라이브러리는 불필요하다 — 의존성 최소주의. 같은 거점의 여러 사건은 마커 하나에 사건 목록 팝업으로 묶어라.
- **경로 폴리라인:** 생애 이동 경로(평양→서울→샌프란시스코→리버사이드→상하이 등)는 시간순 폴리라인으로. 경로 애니메이션은 motion-reduce 대응 필수(4절).
- **시기 슬라이더:** 슬라이더는 `<input type="range">` 기반으로 만들어 키보드(화살표 키)가 공짜로 동작하게 하라. 커스텀 div 슬라이더는 접근성을 처음부터 다시 구현해야 하는 부채다. 슬라이더 변경 시 해당 시기의 마커·경로만 표시.

## 3. 성능

- **이벤트 위임:** 카드 60+개에 리스너를 개별 부착하지 말고 컨테이너 1개에 위임하라. 리스너 수가 사건 수에 비례하면 데이터 증가가 곧 성능 저하다.

```js
container.addEventListener('click', (e) => {
  const card = e.target.closest('[data-event-id]');
  if (card) openDetail(card.dataset.eventId);
});
```

- **렌더링 전략을 먼저 결정하고 코딩하라:** 60~100개 수준이면 전체 렌더 + CSS 표시 토글로 충분하다. 가상 스크롤 같은 복잡한 기법은 측정으로 필요가 입증될 때만 — 추측 기반 최적화는 복잡도만 산다.
- **상세 패널 콘텐츠는 지연 렌더:** 열릴 때 생성. 모든 사건의 상세 DOM을 미리 만들면 초기 로드가 무거워진다.
- **DOM 일괄 삽입:** 카드 생성은 DocumentFragment에 모아 1회 삽입 — 개별 appendChild 반복은 레이아웃 스래싱을 만든다.

## 4. 폴백

인터랙션은 향상(enhancement)이지 전제가 아니다. 실패 모드마다 폴백을 설계하라.

- **비JS:** `<noscript>`에 사건의 정적 목록(연표) / 거점 목록(지도)을 제공. 데이터가 fetch로만 오므로 noscript 본문은 빌드 시점이 아닌 작성 시점에 핵심 사건 요약 목록으로 직접 작성하거나, 최소한 "JS 필요" 안내 + 생애 페이지 링크를 제공하라.
- **motion-reduce:** 모든 애니메이션(경로 그리기, 스크롤 연동, 카드 등장)은 다음으로 감싸라. 전정 장애 사용자에게 모션은 단순 취향 문제가 아니라 신체 증상을 유발한다.

```css
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
```

  JS 애니메이션은 `matchMedia('(prefers-reduced-motion: reduce)')`를 확인해 결과 상태로 즉시 점프시켜라 — 애니메이션을 끄되 결과는 보여야 한다.
- **데이터 로드 실패:** loader.js의 에러 표시를 그대로 사용 — 빈 연표/빈 지도를 침묵 속에 두지 마라.

## 5. 키보드 접근성

- 모든 인터랙티브 요소(카드, 필터, 슬라이더, 마커)는 Tab 도달 + Enter/Space 작동이 가능해야 한다. 클릭 리스너만 단 `<div>`는 키보드 사용자에게 존재하지 않는 UI다 — 카드의 클릭 대상은 `<button>` 또는 `<a>`로.
- 포커스 표시(`:focus-visible`)를 절대 제거하지 마라. 디자인상 거슬리면 outline을 단청색으로 스타일하라 — 제거가 아니라 디자인이 답이다.
- Leaflet 마커는 기본적으로 키보드 포커스 가능하지만, 팝업 내용까지 Tab 순서에 들어가는지 실제 키보드로 전수 시연하라.
- 시기 점프 내비·필터 변경 시 결과 변화를 `aria-live="polite"` 영역으로 알려라 — 시각 변화는 스크린리더에 보이지 않는다.

```html
<div id="filter-status" aria-live="polite" class="visually-hidden"></div>
```

```js
function applyFilter(predicate) {
  let visible = 0;
  for (const card of cards) {
    const show = predicate(card.dataset);
    card.hidden = !show;
    if (show) visible++;
  }
  document.getElementById('filter-status').textContent = `사건 ${visible}건 표시 중`;
}
```

## 산출물 검증

1. **스키마 소비 검증:** 컴포넌트 JS가 참조하는 모든 필드(`event.xxx`, `place.xxx`)를 추출해 timeline.json 실제 필드와 대조 — 없는 필드 참조는 즉시 결함 (web-qa-protocol의 경계면 교차 비교 사용).
2. **동작 검증:** `python3 -m http.server`로 서빙해 필터·상세 패널·슬라이더를 실제 조작. 콘솔 에러 0건 확인.
3. **키보드 전수 시연:** 마우스 없이 Tab/Enter/Esc/화살표만으로 모든 기능을 1회 완주 — 도달 불가 요소가 있으면 결함.
4. **폴백 검증:** JS 비활성 상태에서 noscript 내용 표시 확인, OS 모션 감소 설정에서 애니메이션이 결과 상태로 점프하는지 확인.
5. **불확실성 표시 검증:** disputed/precision/lunar 사건 표본을 골라 화면 표기가 데이터의 정밀도와 일치하는지 대조 — 데이터보다 정밀하게 표시하고 있으면 결함이다.
