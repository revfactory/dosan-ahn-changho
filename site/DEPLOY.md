# 배포 가이드 (DEPLOY.md)

도산 안창호 일대기 정적 사이트의 프로덕션 호스팅 지침. 작성: performance-optimizer (Phase 5, 수정 라운드 1).
이 사이트는 빌드 도구 없는 순수 정적 사이트다(HTML + ES module + fetch JSON). 서버 측 요구사항은 **정적 파일 서빙 + 전송 압축** 뿐이다.

## 0. 한 줄 요약

**프로덕션에서는 gzip 또는 brotli 전송 압축을 반드시 켜라.** 이 한 가지로 전 10페이지가 첫 로드 성능 예산(<200KB, 이미지 제외)을 통과한다. 압축을 끄면 9/10 페이지가 예산을 위반한다(실측).

## 1. 압축이 필수인 이유 (측정 근거)

데이터 JSON은 텍스트라 압축률이 매우 높다(실측):

| 파일 | raw | gzip | 절감 |
|---|---:|---:|---:|
| data/timeline.json | 529.7K | 95.1K | 82% |
| data/network.json | 134.8K | 30.0K | 78% |
| data/citations.json | 83.2K | 14.1K | 83% |
| data/images.json | 82.4K | 13.5K | 84% |

첫 로드 전송량의 지배 요인이 JSON이므로, 압축 여부가 예산 통과/위반을 가른다.

## 2. 압축 기준 페이지별 예상 전송량 (이미지 제외, 예산 < 200KB)

각 자산을 개별 gzip(-9)한 뒤 합산한 실측 추정값:

| 페이지 | raw(무압축) | **gzip 전송** | 예산 |
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
| map.html | 847.1K | 169.9K | OK |

**압축 활성화 시 10/10 페이지 통과.** brotli는 gzip보다 텍스트에서 추가 15~20% 더 줄어 여유가 더 커진다.

## 3. 미리보기 vs 프로덕션

- **로컬 미리보기:** `cd site && python3 -m http.server 8000` → http://localhost:8000
  - `python3 -m http.server`는 **전송 압축을 하지 않는다**(응답에 `Content-Encoding` 없음, `Content-Length`가 raw 크기). 따라서 로컬 미리보기의 전송량은 위 표의 "raw" 열이며, **성능 예산 판정 기준이 아니다.** file:// 직접 열기는 fetch가 CORS로 차단되므로 반드시 로컬 서버로 열 것.
- **프로덕션:** 아래 4절의 압축을 켠 정적 호스트. 성능 예산 판정 기준은 위 표의 "gzip 전송" 열.

## 4. 호스트별 압축 설정

### Nginx
```nginx
gzip on;
gzip_types text/html text/css application/javascript application/json image/svg+xml;
gzip_min_length 1024;
gzip_comp_level 6;
# brotli 모듈이 있으면 추가:
# brotli on; brotli_types text/html text/css application/javascript application/json;
```

### Apache (.htaccess)
```apache
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css application/javascript application/json image/svg+xml
</IfModule>
```

### Netlify / Cloudflare Pages / Vercel / GitHub Pages
- gzip/brotli가 **기본 활성화**되어 있다. 별도 설정 없이 위 예상치대로 전송된다. 배포 후 응답 헤더에 `content-encoding: br` 또는 `gzip`이 있는지만 확인하라.

### 캐시(권장, 선택)
```
# 불변 자산(해시 없는 정적이므로 보수적으로)
Cache-Control: public, max-age=3600        # html
Cache-Control: public, max-age=86400       # css/js/json (배포 시 갱신)
Cache-Control: public, max-age=2592000     # assets/images/*.webp (파일명 안정)
```

## 5. 배포 후 확인 (1분)

```bash
# 압축 적용 확인 — content-encoding 헤더가 보여야 한다
curl -sI -H "Accept-Encoding: gzip,br" https://<배포도메인>/data/timeline.json | grep -i content-encoding
# 끊어진 링크 0건
python3 .claude/skills/web-qa-protocol/scripts/check_links.py site/
```

## 6. 외부 CDN 의존 (map.html 한정)

- Leaflet 1.9.4 CSS·JS를 unpkg.com에서 로드한다. **SRI(integrity sha256) + crossorigin 부착 확인됨** — 변조 방어 OK. 버전 고정 URL이라 CDN 장기 캐시가 적용된다.
- 폰트: Google Fonts(Noto Serif KR) + Pretendard(jsdelivr). 전 페이지 공통. `preconnect` 힌트는 index/timeline/map에 존재.
- 가용성: unpkg/CDN 장애 시에도 map.html은 `<noscript>` 폴백 + `window.L` 부재 시 폴백 안내가 구현되어 빈 화면은 방지된다.
- (선택 강화) unpkg 가용성 의존을 없애려면 Leaflet을 셀프 호스팅(`site/vendor/leaflet/`)으로 전환 가능. 우선순위 낮음.

## 7. 향후 성능 과제 (현재 미적용 — 압축만으로 예산은 이미 통과)

압축으로 예산은 통과하므로 아래는 **선택적 추가 개선**이다. 모두 데이터 로드 경로/구조 변경이라 적용 시 qa-engineer 재검증(데이터 스키마·각주 무결성·콘솔)이 필수다.

- **P1. timeline.json(530K) 분할** — 목록 인덱스(id·title·date·period·tags·좌표)와 상세(서술·출처·상충)를 분리, 상세는 연표 dialog 열 때 지연 fetch. map은 좌표 보유 113건 슬라이스만. timeline.html은 이미 상세 패널 지연 렌더 구조라 데이터만 분리하면 됨.
  - 소유: data-engineer(분할 산출) + timeline-developer/map-developer(소비).
- **P2. citations.json(83K) 페이지별 슬라이스** — 페이지 본문이 쓰는 ref만(측정: timeline 1%·gallery 0%·home 8%). references.html은 전체 sources 렌더가 본질이라 분할 예외.
- **P3. images.json(82K) 페이지별 슬라이스** — 페이지는 자기 슬롯 prefix만 소비(home 4·life 13·org 7…). gallery만 전체 로드.
- **P4. CSS/JS minify** — gzip 적용 후 잔여 효과가 작아 우선순위 낮음. 위반 요인 아님.

## 8. 이미지 운영 메모

- `assets/images/*.webp`(80장)가 표시용. **모든 webp ≤ 200KB**(수정 라운드 1에서 15장 리사이즈 완료). 갤러리/본문 이미지는 `loading="lazy"`로 첫 로드 예산에 들어가지 않는다.
- `assets/images/originals/`(고해상 원본, 80장 ~77MB)는 **배포 산출물이 아니다** — 사이트 코드 어디서도 참조하지 않으며(참조 0건 검증), 재변환·롤백용 보존본이다. 정적 호스트에 통째로 올릴 필요는 없으나, 올라가더라도 어떤 페이지도 첫 로드에 끌어오지 않는다.
