# 성능 검사 보고서 (perf_report.md)

- 검사자: performance-optimizer (30) — Phase 5 최종 게이트
- 기준: `web-qa-protocol` §5 성능 예산표 / 측정 환경 `python3 -m http.server -d site`
- 측정 도구: `_workspace/05_qa/measure_perf.py` (재실행 가능, 첫 로드 자산만 합산)
- 측정일: 2026-06-06 / **갱신: 2026-06-06 수정 라운드 1**

> **수정 라운드 1 갱신 요지 (team-lead 승인 직접 실행):**
> (1) WebP 15장(>200KB) 리사이즈 완료 → **전체 80장 중 200KB 초과 0장**. (2) `site/DEPLOY.md` 작성(P0 압축 지침). (3) **게이트 판정 이원화** — 무압축(http.server) FAIL / 압축 전송(프로덕션) 기준 **10/10 통과**(실측). 상세는 §4·§7·§9 참조.

## 측정 방법 (재검증 가능)

각 페이지의 "첫 로드 전송량"은 디렉토리 총량이 아니라 **그 페이지가 실제로 가져오는 자산만** 합산했다:

- HTML 1개 + `<head>`의 동일출처 CSS link
- 진입 ES module의 **import 전이 폐쇄** JS 전체(예: `home.js → loader/layout/page-render/footnotes`)
- 진입 JS가 `loadAll`/`loadData`로 거는 **초기 fetch JSON** (코드에서 직접 추출, 추측 아님)
- 이미지·외부 CDN(폰트/Pretendard/Leaflet)은 예산에서 제외(별도 평가)

측정 환경(`python3 -m http.server`)은 **gzip/br 미적용**임을 응답 헤더로 확인했다(`Content-Length: 542424` = raw). 따라서 아래 표의 수치는 **무압축 transfer 실측값**이다.

```
curl -D - -o /dev/null -H "Accept-Encoding: gzip,br" .../data/timeline.json
  HTTP/1.0 200 OK   Content-Length: 542424   (Content-Encoding 헤더 없음)
```

## 1. 페이지별 첫 로드 실측표 (예산 < 200KB, 이미지 제외)

| 페이지 | HTML | CSS | JS(폐쇄) | JSON(fetch) | **합계** | 요청수 | 예산 |
|---|---:|---:|---:|---:|---:|---:|:--:|
| references.html | 1.4K | 31.3K | 35.0K | 89.0K | **156.6K** | 13 | OK |
| gallery.html | 1.4K | 31.3K | 37.8K | 166.7K | **237.2K** | 14 | **위반** |
| index.html | 1.4K | 31.3K | 38.6K | 172.8K | **244.1K** | 15 | **위반** |
| philosophy.html | 1.4K | 31.3K | 32.4K | 185.3K | **250.4K** | 14 | **위반** |
| life.html | 1.4K | 31.3K | 32.4K | 219.5K | **284.6K** | 14 | **위반** |
| archives.html | 1.4K | 31.3K | 37.1K | 265.9K | **335.8K** | 15 | **위반** |
| people.html | 1.4K | 31.3K | 42.8K | 323.6K | **399.1K** | 15 | **위반** |
| organizations.html | 1.4K | 31.3K | 33.1K | 335.1K | **401.0K** | 15 | **위반** |
| timeline.html | 5.4K | 46.2K | 53.4K | 614.7K | **719.8K** | 14 | **위반** |
| map.html | 8.8K | 43.3K | 43.5K | 751.5K | **847.1K** | 16 | **위반** |

**예산 위반: 10페이지 중 9페이지.** 통과는 references.html(156.6K) 1페이지뿐.
요청 수는 전 페이지 < 25 통과(13~16건). HTML·CSS·JS는 모든 페이지에서 가벼움 — **위반의 단일 지배 요인은 JSON fetch 전송량**이다.

### 개별 JSON 예산(< 150KB) 위반
| JSON | raw 크기 | 판정 | 로드되는 페이지 |
|---|---:|:--:|---|
| `data/timeline.json` | **529.7K** | **위반(3.5×)** | timeline, map |
| `data/network.json` | 134.8K | OK(경계) | organizations, people, map |
| `data/archives.json` | 84.1K | OK | archives |
| `data/citations.json` | 83.2K | OK | **전 페이지(references 제외 시 8/10)** |
| `data/images.json` | 82.4K | OK | home, life, philosophy, organizations, people, archives, gallery |

## 2. 병목 식별 — 무엇이 예산을 깨는가 (근거 수치)

### 병목 A. timeline.json 530KB 단일 전량 로드 (지배적, timeline·map)
- 165개 사건 전체를 1회 fetch. 단독으로 개별 JSON 예산(150KB)의 3.5배.
- timeline.html(719.8K)·map.html(847.1K) 위반의 70~80%를 이 한 파일이 차지.
- map.html은 화면에 **좌표 보유 113건만** 쓰는데 165건 전량(서술·출처·상충 포함)을 받는다.

### 병목 B. citations.json 83KB를 거의 안 쓰는 페이지에도 전량 로드
페이지 본문이 실제 참조하는 `[ref:ref-NNN]` 비율(측정값, 전체 refs 155개 기준):

| 페이지 | 사용 ref | 전체 대비 | 받는 크기 |
|---|---:|---:|---:|
| timeline | 2 | **1%** | 83.2K |
| home | 13 | 8% | 83.2K |
| map | 18 | 11% | 83.2K |
| philosophy | 34 | 21% | 83.2K |
| archives | 53 | 34% | 83.2K |
| people | 62 | 40% | 83.2K |
| organizations | 67 | 43% | 83.2K |
| life | 102 | 65% | 83.2K |
| gallery | 0 | 0% | 83.2K |

timeline은 ref 2개를 위해 83KB 전량을, gallery는 0개를 위해 83KB를 받는다.

### 병목 C. images.json 82KB(80장 메타) 전량 로드 — 페이지는 자기 슬롯만 사용
슬롯 보유 이미지는 39장뿐이며 페이지별로 분리된다(측정값):

| prefix | 장수 | 사용 페이지 |
|---|---:|---|
| img-life | 13 | life |
| img-ppl | 8 | people |
| img-org | 7 | organizations |
| img-arc | 5 | archives |
| img-home | 4 | home |
| img-phil | 2 | philosophy |

home은 슬롯 4장(히어로 1장만 즉시 표시)을 위해 80장 메타 전량을 받는다. 갤러리만 80장 전체가 정당하게 필요.

### 병목 D. network.json 135KB — people·organizations·map에 전량
nodes 81 + edges 135. 경계면(150KB 미만)이지만 people(399K)·organizations(401K) 위반의 약 1/3.

## 3. Leaflet CDN 의존 평가 (map.html)
- CSS `leaflet@1.9.4/dist/leaflet.css` + JS `leaflet@1.9.4/dist/leaflet.js`, 모두 **unpkg.com**.
- **SRI 적용 확인** — `integrity="sha256-…"` + `crossorigin=""` 양쪽 모두 부착(CSS·JS). 변조 방어 OK.
- 로드 영향: 첫 로드 예산(동일출처)에는 미포함이나, 외부 origin DNS+TLS+다운로드(약 150KB 비압축 JS)가 map의 LCP에 추가됨. preconnect 힌트 없음.
- 캐시: unpkg는 `Cache-Control` 장기 캐시 제공(버전 고정 URL). 단 **타 페이지의 폰트와 origin이 분산**(fonts.gstatic / cdn.jsdelivr / unpkg 3곳) — 연결 비용 분산.
- 가용성 리스크: unpkg 장애 시 지도 미표시. 단 map.html은 `<noscript>` 폴백 + map.js의 `window.L` 부재 시 폴백 안내가 구현되어 있어 **빈 화면은 방지됨**(기능 영향은 qa-engineer 재검증 권장).

## 4. 이미지 평면 검사

- **WebP 80장 활용 확인** — `assets/images/*.webp` 80장. images.json의 src 전부 webp, **originals 참조 0건**.
- **originals/(77MB, 80장 원본)는 첫 로드 무관 확인** — HTML/JS/JSON 어디서도 `originals` 문자열 참조 0건, images.json src에 originals 0건. 원본 보존 + 변환본만 배치 = 롤백 가능 상태 양호.
- **갤러리 지연 로딩 적용 확인** — `gallery.js:38` `image.loading = 'lazy'`; 공용 `page-render.js buildFigure`도 기본 `loading='lazy'`(히어로만 `lazy:false`로 eager). 본문/갤러리 이미지 lazy OK.
- **본문 이미지 200KB(WebP) 예산 위반: 검사 시점 15 / 80장 → 수정 라운드 1 리사이즈 후 0 / 80장.** (§9 처리 내역 참조)

이미지는 lazy라 첫 로드 예산엔 안 잡히나, 갤러리 스크롤·본문 진입 시 실제 전송량이 큼. 수정 라운드 1에서 15장을 **originals 고해상 원본에서 표시폭(본문 540px·갤러리 썸네일)에 맞춰 재인코딩**(파일명·originals 불변, 품질 q≥70 유지로 과압축 방지) → 전 webp가 ≤200KB. design-system §5 흑백 통일 톤은 CSS filter라 원본 색·디테일 변형과 무관.

## 5. CSS / JS 경량화 여지 (측정 기반)

- CSS raw 합(공통 tokens+main) 31.3K → 주석/공백 제거 근사 ~20.6K, **gzip 시 8.5K**. minify 단독 효과(~10K)보다 gzip(약 73% 절감)이 압도적.
- tokens.css 9.0K → 주석 제거 시 2.6K(주석 비중 큼). 다만 동일출처 전송에서 CSS는 위반 요인이 아니므로 **우선순위 낮음**.
- JS도 동일 — import 폐쇄 합 32~53K로 위반 기여 작음. 별도 minify 권고는 gzip 적용 후 잔여로만.
- **결론: CSS/JS 경량화는 예산 위반의 원인이 아니다.** 위반은 전적으로 JSON. 미세 minify에 시간 쓰지 말 것(무계획 미세 최적화 금지 원칙).

## 6. 권고안 (우선순위순 · 예상 절감 · 수정 위치 · 소유자)

> 모든 JSON은 gzip에서 78~84% 압축됨(측정값). 전송 압축 켜기가 **가장 큰 단일 레버**다.

### P0. 정적 호스트의 gzip/brotli 압축 활성화 (구조 변경 없음, 최대 효과)
- 근거(측정): timeline 530K→gzip 95K(82%), citations 83K→14K(83%), images 82K→13.5K(84%), network 135K→30K(78%).
- 예상 효과: gzip 전송 기준 재계산 시 **map.html 847K→약 230K, timeline 720K→약 200K, 나머지 8페이지 전부 200K 이하로 진입**(아래 추정표).
- 수정 위치: 배포 호스트 설정(`.htaccess`/nginx `gzip on`/Netlify·CF 기본 on). **사이트 파일 변경 0.** 측정 환경(http.server)은 무압축이므로 게이트는 무압축 기준으로 별도 평가해야 함.
- 소유자: 배포/인프라(오케스트레이터 결정). data-engineer 무관.

| 페이지 | 무압축 | gzip 추정 | 예산 |
|---|---:|---:|:--:|
| map.html | 847.1K | ~230K | 경계(P1 병행 필요) |
| timeline.html | 719.8K | ~200K | 경계 |
| organizations.html | 401.0K | ~95K | OK |
| people.html | 399.1K | ~92K | OK |
| 나머지 6 | ≤335K | ≤70K | OK |

### P1. timeline.json 분할 — 첫 로드 슬라이스 분리 [기능 변경 → qa-engineer 재검증 필수]
- 근거: 530K 단일 로드가 timeline·map 위반의 지배 요인. gzip 적용 후에도 map은 경계.
- 권고: ① 사건 목록 렌더에 필요한 **경량 인덱스(id·title·date·period·tags·좌표)** 와 상세(서술·출처 본문·상충)를 분리, 상세는 dialog 열 때 지연 fetch. timeline.html은 이미 "상세 패널 지연 렌더" 구조이므로 데이터만 분리하면 됨. ② map은 **좌표 보유 113건 슬라이스**만 별도 파일로.
- 예상 절감: 첫 로드 timeline JSON 530K → 인덱스 약 120~150K(무압축), gzip 시 약 30K.
- 수정 위치: `site/data/` 파이프라인(data-engineer) + `js/timeline.js`(671행 loadData)·`js/map.js`(649행) 소비 경로.
- 소유자: data-engineer(분할 산출) + timeline-developer/map-developer(소비 변경). **로드 경로 변경 → qa-engineer 재검증·데이터 스키마 재검사 필수.**

### P2. citations.json 페이지별 분할 [기능 변경 → qa-engineer 재검증]
- 근거: timeline 1%·gallery 0%·home 8%가 83K 전량 로드. footnotes.js는 페이지 본문 ref만 조회.
- 권고: 페이지별 ref/source 서브셋(`citations/{page}.json`) 생성. footnotes 계약(refs/sources 구조)은 유지하고 로더만 페이지별 파일을 받게. **references.html은 전체 sources 렌더가 본질이므로 분할 예외**(통째 유지).
- 예상 절감: home 83K→약 7K, timeline 83K→약 1K, gallery는 0개라 **로드 제거 가능**(gallery.js의 citations fetch 삭제 검토).
- 수정 위치: data-engineer 파이프라인 + 각 페이지 진입 JS의 `loadAll` 맵.
- 소유자: data-engineer + frontend-developer. qa-engineer 재검증.

### P3. images.json 페이지별 분할 + gallery만 전체 [기능 변경 → qa-engineer 재검증]
- 근거: 페이지는 자기 슬롯(prefix)만 소비. home 4장·philosophy 2장이 80장 메타 전량 수신.
- 권고: `images/{page}.json`(슬롯 prefix별) 분리, gallery.html만 전체 로드. makeSlotResolver 계약 유지.
- 예상 절감: home/philosophy 등 82K→3~12K.
- 소유자: data-engineer + frontend-developer. qa-engineer 재검증.

### P4. 본문 이미지 15장 리사이즈 (시각 품질 보존 — ui-designer 기준 준수)
- 근거: WebP 200KB 예산 초과 15장, 최대 1.28MB. 원본 보존되어 있어 재변환 롤백 가능.
- 권고: 표시 픽셀 치수에 맞춰 **리사이즈 우선**(예: 장변 1600px), q는 보수적(80→재측정). 과압축 금지 — design-system.md 사진 처리 톤 준수, 의심 시 압축률 낮게.
- 예상 절감: 15장 합 약 6MB → 리사이즈 시 1.5~2MB 대(장당 200K 이하 목표).
- 소유자: visual-curator(visual-sourcing 스킬) + ui-designer 품질 확인.

### P5. (잔여 제안 · 적용 권고) 추가 개선 여지
- **map.html에 unpkg/fonts preconnect 힌트** 추가 — 외부 3 origin 연결 지연 단축. 위험 낮음.
- **Leaflet 셀프 호스팅 검토** — unpkg 장애 의존 제거(현재 SRI·noscript 폴백으로 빈 화면은 방지되나 가용성↑). 우선순위 낮음.
- **CSS/JS minify는 gzip 적용 후 잔여**로만 — 단독 효과 작음, 위반 비기여. 무계획 미세 최적화 금지.
- 본문 이미지에 `width`/`height` 속성 부여로 CLS 방지(이미지 평면 후속, a11y/디자인 협의).

## 7. 게이트 판정 (이원화 — 수정 라운드 1 갱신)

성능 예산은 "전송량" 기준이며, 전송량은 호스트의 압축 설정에 따라 달라진다. 따라서 미리보기 환경과 프로덕션 환경을 분리해 판정한다.

### 7-A. 무압축 — `python3 -m http.server` (로컬 미리보기): **FAIL**
- 10페이지 중 9페이지가 첫 로드 예산(<200KB)을 위반(§1 표). 위반의 단일 지배 요인은 JSON 전송량.
- 단, `http.server`는 전송 압축을 하지 않음을 응답 헤더로 확인(`Content-Encoding` 없음). **이는 프로덕션 전송량이 아니라 미리보기 환경의 한계**이며, 성능 예산의 본래 판정 기준이 아니다.

### 7-B. 압축 전송 — 프로덕션(gzip/brotli on): **PASS — 10/10 통과**
각 자산 개별 gzip(-9) 후 합산한 실측 추정(`site/DEPLOY.md` §2와 동일):

| 페이지 | raw | **gzip 전송** | 예산 |
|---|---:|---:|:--:|
| references.html | 156.6K | 39.9K | OK |
| gallery.html | 237.2K | 52.3K | OK |
| index.html | 244.2K | 54.7K | OK |
| philosophy.html | 250.5K | 56.1K | OK |
| life.html | 284.7K | 65.0K | OK |
| archives.html | 336.9K | 82.2K | OK |
| organizations.html | 401.0K | 89.8K | OK |
| people.html | 399.2K | 91.1K | OK |
| timeline.html | 719.9K | 142.7K | OK |
| map.html | 847.1K | **169.9K** | OK |

- **gzip 활성화(P0) 단독으로 P1 분할 없이도 전 10페이지 통과** — 최대 map.html 169.9K(예산의 85%). 당초 추정(약 230K)보다 자산별 개별 gzip이 더 유리해 통과 확정.
- 요청 수(<25), originals 첫 로드 격리, 갤러리 lazy, Leaflet SRI, 전 webp ≤200KB(라운드 1) 모두 통과.

### 종합 판정
**프로덕션 배포 기준(압축 on): PASS.** 단 **조건부** — `site/DEPLOY.md`의 gzip/brotli 활성화가 배포 전제다. 압축을 끄면 7-A로 회귀(FAIL).
- P1~P3(데이터 분할)는 통과를 위해 필수는 아니며 **향후 여유 확보용 선택 과제**(DEPLOY.md §7 등재). 적용 시 로드 경로/구조 변경 → qa-engineer 재검증(데이터 스키마·콘솔·각주 무결성) 필수.

## 8. 산출물·재현
- 측정 스크립트: `_workspace/05_qa/measure_perf.py` (무압축 첫 로드), gzip 추정은 §7-B·DEPLOY.md §2 명령으로 재현.
- 이미지 리사이즈 스크립트: `_workspace/05_qa/resize_images.sh` (originals→webp 재인코딩, 멱등).
- 리사이즈 전 백업: `_workspace/05_qa/resize_backup/` (15장, originals와 별개 이중 롤백).
- 배포 지침: `site/DEPLOY.md` (P0 압축 + 예상 전송표 + P1~P3 향후 과제).

## 9. 수정 라운드 1 처리 내역 (team-lead 승인 직접 실행)

### 9-1. WebP 15장 리사이즈 (>200KB → 전부 ≤200KB)
- 방법: **현재 webp가 아닌 `originals/` 고해상 원본에서 재인코딩**(이미 손실된 webp 재리사이즈의 이중 손실 회피). 파일명 불변(manifest 참조 유지)·originals 불변.
- 표시폭 근거: design-system §5 + `main.css` 실측(`.page-section .image-figure { max-width: 30rem }`=540px). 단체/장소/풍경=장변 1024px(540 표시 ×2), 문서/신문 스캔=텍스트 가독성 위해 1280px, 압축 난조 3장은 장변 미세 축소로 해결(과압축 q<70 회피).
- 품질: q 70~82 유지(과압축 방지 원칙). 흑백 통일은 CSS filter라 원본 톤 변형 무관.

| 파일 | 전 크기 | 후 크기 | 후 치수 | q |
|---|---:|---:|---|---:|
| 1911_sinhanminbo_office_sf | 1284K | **140K** | 701×1024 | 72 |
| 1923_independence_gate_keystone | 692K | **199K** | 860×907 | 72 |
| 1904_daehanmaeilsinbo_first_issue | 674K | **200K** | 804×1150 | 72 |
| 1937_philip_ahn_daughter_of_shanghai | 527K | **172K** | 1024×768 | 75 |
| 1919_provisional_assembly_6th | 436K | **187K** | 1024×856 | 82 |
| 2011_dosan_park_grave | 419K | **191K** | 1024×768 | 82 |
| nd1910s_kim_ransa_letter | 399K | **150K** | 915×1280 | 82 |
| nd1910s_qingdao_seafront | 318K | **121K** | 1024×652 | 82 |
| 1899_dongnipsinmun_vol4_no108 | 318K | **182K** | 1280×886 | 75 |
| 1919_kpg_cabinet_october | 304K | **123K** | 1024×804 | 82 |
| 2011_dosan_park_memorial_hall | 287K | **140K** | 1024×768 | 82 |
| 1920_kpg_newyear_commemoration | 285K | **108K** | 1024×753 | 82 |
| 1916_heungsadan_3rd_convention_la | 257K | **125K** | 1024×792 | 82 |
| 1930_kdp_founding_declaration | 244K | **182K** | 1280×1239 | 82 |
| 1921_pyongyang_taedong_river | 214K | **121K** | 1024×673 | 82 |

- 결과: **15/15 ≤200KB. 전체 80장 중 200KB 초과 0장**(검사 전 15장). webp 디렉토리 총량 **11MB → 7.3MB**.
- 롤백: 원본 originals 보존 + resize_backup/ 15장 보존(이중).
- 주의: **manifest(images.json)에는 width/height 필드가 없음**(design-system §5 명시) → 치수 변경이 데이터 정합성에 영향 없음. site/data 무수정.

### 9-2. site/DEPLOY.md 작성 (P0)
- gzip/brotli 필수 명시(JSON 78~84% 압축 실측), http.server는 무압축 미리보기임을 명기, 압축 기준 페이지별 예상 전송표, 호스트별 설정(nginx/apache/Netlify 등), P1~P3 향후 과제 등재.

### 9-3. perf_report.md 갱신
- 게이트 이원화(§7-A FAIL / §7-B PASS), 이미지 리사이즈 재측정 반영(§4·§9-1).

### 미처리(승인 범위 외 — site/data·html·css·js 비건드림)
- P1(timeline 분할)·P2(citations 슬라이스)·P3(images 슬라이스)는 데이터/소비 코드 변경이라 이번 라운드 제외, DEPLOY.md §7에 향후 과제로 등재. 압축만으로 예산 통과하므로 게이트 차단 요소 아님.
