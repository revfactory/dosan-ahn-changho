#!/usr/bin/env bash
# resize_images.sh — perf round 1: WebP 15장 리사이즈 (>200KB)
# 원본(originals/*.{jpg,png})에서 재인코딩(webp 재리사이즈 이중손실 회피).
# 파일명 불변(manifest 참조 유지) · originals/ 불변. 표시폭 근거 design-system §5 + main.css 실측.
#   본문 figure max-width 30rem(540px) → 2x 여유 장변 1024px (단체/장소/풍경)
#   문서/신문 스캔 = 텍스트 가독성 → 장변 1280px (확대보기 허용 범위 내 보수적)
# 품질 q=82 기본, 결과 >200KB면 q를 75→70으로 단계 하향(과압축 방지, 70 하한).
set -euo pipefail
cd "$(dirname "$0")/../../site/assets/images"
ORIG=originals
TARGET_KB=200

# stem  longedge
declare -a JOBS=(
  # 문서/신문 스캔 (텍스트 가독성) → 1280
  "1904_daehanmaeilsinbo_first_issue 1280"
  "1899_dongnipsinmun_vol4_no108 1280"
  "nd1910s_kim_ransa_letter 1280"
  "1930_kdp_founding_declaration 1280"
  "1911_sinhanminbo_office_sf 1280"
  # 단체/장소/풍경 사진 → 1024
  "1923_independence_gate_keystone 1024"
  "1937_philip_ahn_daughter_of_shanghai 1024"
  "1919_provisional_assembly_6th 1024"
  "2011_dosan_park_grave 1024"
  "nd1910s_qingdao_seafront 1024"
  "1919_kpg_cabinet_october 1024"
  "2011_dosan_park_memorial_hall 1024"
  "1920_kpg_newyear_commemoration 1024"
  "1916_heungsadan_3rd_convention_la 1024"
  "1921_pyongyang_taedong_river 1024"
)

printf "%-44s %-12s %-12s %8s -> %8s\n" "file" "src->dst px" "q" "before" "after"
for job in "${JOBS[@]}"; do
  stem=${job% *}; edge=${job##* }
  src=$(ls "$ORIG/$stem".* 2>/dev/null | head -1)
  dst="$stem.webp"
  [ -z "$src" ] && { echo "  !! $stem 원본 없음 — 건너뜀"; continue; }
  before=$(( $(wc -c < "$dst") / 1024 ))
  srcdim=$(magick identify -format "%wx%h" "$src")
  # 장변이 edge보다 작으면 확대 금지(원본 유지폭)
  for q in 82 75 70; do
    # >longedge 면 축소만(확대 금지), 비율 유지
    cwebp -quiet -q "$q" -resize 0 0 "$src" -o /tmp/_rs_probe.webp >/dev/null 2>&1 || true
    # 장변 기준 리사이즈: 가로>세로면 -resize edge 0, 아니면 -resize 0 edge
    w=${srcdim%x*}; h=${srcdim#*x}
    if [ "$w" -ge "$h" ]; then rs="-resize $edge 0"; else rs="-resize 0 $edge"; fi
    # 원본 장변이 edge 이하면 리사이즈 생략(확대 금지)
    long=$(( w > h ? w : h ))
    if [ "$long" -le "$edge" ]; then rs=""; fi
    cwebp -quiet -q "$q" $rs "$src" -o "$dst" >/dev/null 2>&1
    after=$(( $(wc -c < "$dst") / 1024 ))
    [ "$after" -le "$TARGET_KB" ] && break
  done
  dstdim=$(magick identify -format "%wx%h" "$dst")
  printf "%-44s %-12s q=%-10s %6sK -> %6sK\n" "$stem" "$dstdim" "$q" "$before" "$after"
done