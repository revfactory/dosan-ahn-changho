---
name: site-architecture
description: 빌드 도구 없는 정적 사이트의 기술 스택, 디렉토리 구조, 페이지 구성 표준, 데이터 로더 패턴, 인터페이스 계약, 파일 소유권 규칙을 정의하는 스킬. content-architect(16)가 사이트맵·IA를 설계할 때, web-architect(21)가 architecture.md를 작성할 때, data-engineer(23)가 site/data 변환 파이프라인을 만들 때, frontend-developer(24)가 페이지를 구현할 때 반드시 사용하라. "구조 변경", "스키마 업데이트", "계약 수정", "디렉토리 재정리", "데이터 파이프라인 보완" 같은 후속 요청에도 이 스킬을 먼저 다시 읽고 계약 위반 여부를 점검하라.
---

# 사이트 설계 (site-architecture)

도산 안창호 웹사이트의 기술적 뼈대를 정의한다 — 무엇으로 만들고, 어디에 무엇을 두고, 모듈끼리 어떤 약속으로 통신하는가. 여러 에이전트가 같은 코드베이스를 동시에 만지는 환경에서는 "암묵적 합의"가 곧 통합 버그다. 그래서 이 스킬은 모든 경계(스택, 디렉토리, 데이터 스키마, 파일 소유권)를 명시적 계약으로 고정하는 방법을 제공한다.

## 1. 기술 스택 — 빌드 도구 없는 정적 사이트

**확정 스택: HTML + CSS + vanilla JS + JSON 데이터. 외부 라이브러리는 Leaflet(지도)만 CDN으로 허용.**

이 선택의 이유를 이해하고 지켜라.

- **의존성 부패 없음.** npm 의존성 트리는 시간이 지나면 보안 경고·호환성 파괴·설치 실패로 부패한다. 역사 아카이브 사이트는 10년 뒤에도 열려야 하는 산출물이고, 의존성 0인 정적 파일은 부패할 것이 없다.
- **어디서나 서빙 가능.** GitHub Pages, S3, 로컬 디스크, USB — 어떤 정적 호스팅에도 빌드 단계 없이 그대로 올라간다. 배포가 곧 파일 복사다.
- **에이전트 빌드 안정성.** 빌드 도구가 있으면 에이전트는 "코드는 맞는데 빌드가 깨지는" 상태를 디버깅하는 데 턴을 소모한다. 빌드가 없으면 작성한 파일이 곧 실행 결과이므로 실패 지점이 코드 자체로 한정되고, 여러 에이전트의 병렬 작업이 빌드 설정 충돌 없이 합쳐진다.

따라서 추가 라이브러리·프레임워크·번들러 도입은 기본적으로 금지다. 정말 필요하면 web-architect에게 사유서(해결하려는 문제, vanilla로 안 되는 이유, 장기 유지 비용)를 제출해 합의를 받아라. "편해서"는 사유가 아니다.

## 2. 디렉토리 구조

```
site/
├── index.html              홈
├── life.html               생애 (시기별 장)
├── timeline.html           인터랙티브 연표
├── map.html                활동 지도
├── philosophy.html         사상
├── people.html             인물 관계
├── archives.html           사료
├── gallery.html            갤러리
├── references.html         참고문헌
├── css/
│   ├── tokens.css          디자인 토큰 (ui-designer 소유)
│   └── main.css            공통 스타일
├── js/
│   ├── loader.js           공통 데이터 로더
│   ├── layout.js           공통 레이아웃·내비
│   ├── timeline.js         연표 (timeline-developer 소유)
│   └── map.js              지도 (map-developer 소유)
├── data/
│   ├── timeline.json
│   ├── network.json
│   ├── citations.json
│   ├── pages/*.json        페이지 본문 데이터
│   └── images.json         이미지 매니페스트
└── assets/
    └── images/             최적화 이미지 + originals/
```

새 파일이 필요하면 이 구조의 기존 분류에 넣어라. 새 최상위 디렉토리 추가는 web-architect 합의 사항이다 — 구조가 늘어나면 모든 팀원의 탐색 비용이 늘어난다.

## 3. 페이지 구성 표준

모든 페이지는 다음 골격을 공유한다: 공통 헤더(사이트명 + 전역 내비) → 페이지 헤더(h1 + 한 줄 소개) → 본문 섹션들 → 공통 푸터(크레딧 + 참고문헌 링크). 9개 페이지(홈/생애/연표/지도/사상/인물/사료/갤러리/참고문헌)는 전역 내비에 모두 노출하고, 페이지 간 교차 링크(예: 생애 본문의 사건 → 연표 해당 사건 앵커)는 콘텐츠 명세에 정의된 것만 구현하라. 내비게이션 마크업은 한 곳(layout.js 또는 공통 include 패턴)에서만 정의해 페이지마다 복붙하지 마라 — 복붙된 내비는 페이지 추가 시 반드시 한 곳을 빠뜨린다.

## 4. 데이터 로더 패턴

모든 콘텐츠는 `site/data/*.json`에서 fetch로 로드해 렌더링한다. HTML에 콘텐츠를 하드코딩하지 마라 — 하드코딩된 텍스트는 검증 DB(claims_register, timeline.json)와의 대조 경로가 끊겨 content-qa가 잡을 수 없는 오류가 된다.

```js
// js/loader.js — 공통 로더 패턴
export async function loadData(path) {
  try {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${path}`);
    return await res.json();
  } catch (err) {
    // 실패를 삼키지 않는다 — 빈 화면은 디버깅 불가능한 결함이다
    renderLoadError(path, err);
    throw err;
  }
}
```

로드 실패 시 사용자에게 보이는 에러 메시지(`renderLoadError`)를 반드시 구현하라. 콘솔에만 찍히는 에러는 QA 단계에서만 발견되고, 빈 화면은 원인 추적 비용이 크다.

### 로컬 미리보기 — file:// 함정

브라우저는 `file://`로 연 페이지의 fetch를 CORS 정책으로 차단한다. HTML 파일을 더블클릭해 열면 **데이터가 전부 로드 실패**하므로, 이것은 코드 버그가 아니다. 미리보기는 반드시 로컬 서버로 하라.

```bash
cd site && python3 -m http.server 8000
# http://localhost:8000 으로 확인
```

QA·스크린샷·동작 확인도 모두 이 방식을 전제로 한다. file://에서 빈 화면을 보고 코드를 "수정"하지 마라.

## 5. 인터페이스 계약 작성법

모듈 경계(데이터 ↔ 소비 코드, 공통 모듈 ↔ 페이지 코드)는 구현 전에 계약 문서로 고정한다. 계약이 없으면 각 개발자가 필드명을 추측하고, 추측의 불일치가 Phase 4b의 통합 버그가 된다.

`_workspace/04_build/architecture.md`에 다음 형식으로 작성하라.

```markdown
### 계약: timeline.json ↔ timeline.js
- 스키마: { events: [{ id, title, date: {start, end, precision, calendar},
  place: {name, lat, lng}, summary, confidence, disputed, tags[] }] }
- 소비자가 의존하는 필드: id, title, date.start, date.precision, summary, disputed
- null 정책: place.lat/lng는 null 가능 (소비자는 null 시 지도 연결 생략)
- 변경 절차: data-engineer가 web-architect 합의 후 스키마 변경,
  소비자 전원에게 고지, qa-engineer 재검증
```

계약의 핵심 요소: **스키마 전체 + 소비자가 실제로 읽는 필드 목록 + null/누락 정책 + 변경 절차.** 소비 필드 목록을 명시하는 이유는 qa-engineer가 경계면 교차 비교를 할 때 이 목록이 대조 기준이 되기 때문이다.

## 6. 파일 소유권 규칙

동시 수정 충돌은 사후 머지가 아니라 사전 소유권으로 막는다. 모든 `site/` 파일에 단일 소유자를 지정하라.

| 파일 | 소유자 |
|------|--------|
| `css/tokens.css` | ui-designer |
| `js/timeline.js`, `timeline.html` | timeline-developer |
| `js/map.js`, `map.html` | map-developer |
| `data/*.json` | data-engineer |
| 그 외 html/css/js | frontend-developer |

- 소유자가 아닌 파일을 수정해야 하면 소유자에게 요청하라. 직접 수정은 금지다.
- 예외: a11y-engineer는 접근성 위반 수정에 한해 모든 파일을 수정할 수 있되, 수정 내역을 소유자에게 고지한다.
- 공통 모듈(loader.js, layout.js)의 시그니처 변경은 모든 소비자에게 사전 고지 — 시그니처는 계약이다.

## 산출물 검증

1. **architecture.md:** 모든 데이터 파일에 대해 계약(스키마 + 소비 필드 + null 정책 + 변경 절차)이 존재하는지, 파일 소유권 표가 site/ 전체를 커버하는지 확인.
2. **디렉토리:** `site/` 실제 구조가 2절 구조와 일치하는지 `ls -R site/`로 대조. 계약에 없는 파일이 생겼다면 계약 누락이거나 무단 파일이다.
3. **데이터 파이프라인:** 변환 스크립트를 재실행해 같은 출력이 나오는지(재현성), 변환 전후 레코드 수가 일치하는지 확인.
4. **로더 동작:** `python3 -m http.server`로 서빙한 상태에서 각 페이지를 열어 데이터 로드 에러가 0건인지 확인. file://로 검증하지 마라.
5. **하드코딩 검사:** HTML에서 날짜·인명 등 사실 텍스트를 grep으로 표본 검사 — 발견되면 data/로 이동시켜라.
