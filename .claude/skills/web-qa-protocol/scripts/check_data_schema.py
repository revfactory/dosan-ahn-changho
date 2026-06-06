#!/usr/bin/env python3
"""check_data_schema.py — JSON 데이터 필수 필드·타입 전수 검사.

JSON 파일의 모든 레코드에 대해 필수 필드의 존재와 타입을 검사한다.
필수 필드 목록은 인터페이스 계약(architecture.md)에서 가져올 것 —
이 스크립트는 계약의 집행 도구이지 계약의 대체물이 아니다.

사용법:
    python3 check_data_schema.py <json_file> --required <필드[:타입]> ... [--records <키.경로>]

    --required  필수 필드 목록. "이름" 또는 "이름:타입" 형식.
                지원 타입: str, int, float, number, bool, list, dict
                중첩 필드는 점 표기: date.start:str
    --records   레코드 배열이 위치한 키 경로 (점 표기, 예: events).
                생략 시: 최상위가 배열이면 그대로, 객체면 배열 값을 가진
                키가 정확히 1개일 때 그 배열을 사용.

예시:
    python3 check_data_schema.py site/data/timeline.json \\
        --records events \\
        --required id:str title:str date:dict date.start:str summary:str sources:list

종료 코드:
    0 — 전 레코드 통과
    1 — 누락/타입 불일치/파일·인자 오류 존재

표준 라이브러리만 사용한다.
"""

import argparse
import json
import sys

TYPE_MAP = {
    "str": str,
    "int": int,
    "float": float,
    "number": (int, float),
    "bool": bool,
    "list": list,
    "dict": dict,
}


def parse_field_spec(spec: str):
    """'이름' 또는 '이름:타입' → (이름, 검사타입 or None)"""
    if ":" in spec:
        name, type_name = spec.rsplit(":", 1)
        if type_name not in TYPE_MAP:
            raise ValueError(
                f"알 수 없는 타입 '{type_name}' (지원: {', '.join(TYPE_MAP)})"
            )
        return name, TYPE_MAP[type_name]
    return spec, None


def dig(obj, dotted_path: str):
    """점 표기 경로로 중첩 값을 찾는다. (found, value) 반환."""
    current = obj
    for key in dotted_path.split("."):
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return False, None
    return True, current


def find_records(data, records_path):
    """검사 대상 레코드 배열을 찾는다."""
    if records_path:
        found, value = dig(data, records_path)
        if not found:
            raise ValueError(f"--records 경로 '{records_path}'가 존재하지 않음")
        if not isinstance(value, list):
            raise ValueError(f"--records 경로 '{records_path}'의 값이 배열이 아님")
        return value
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        list_keys = [k for k, v in data.items() if isinstance(v, list)]
        if len(list_keys) == 1:
            return data[list_keys[0]]
        raise ValueError(
            "레코드 배열 위치가 모호함 — --records 로 키 경로를 지정하라 "
            f"(배열 값 키: {list_keys or '없음'})"
        )
    raise ValueError("최상위가 배열도 객체도 아님")


def type_name(value) -> str:
    return type(value).__name__


def main() -> int:
    parser = argparse.ArgumentParser(
        description="JSON 레코드 필수 필드·타입 전수 검사",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("json_file", help="검사할 JSON 파일 경로")
    parser.add_argument(
        "--required", nargs="+", required=True,
        metavar="FIELD[:TYPE]", help="필수 필드 목록 (점 표기 중첩 가능)",
    )
    parser.add_argument(
        "--records", default=None, metavar="KEY.PATH",
        help="레코드 배열의 키 경로 (생략 시 자동 탐지)",
    )
    args = parser.parse_args()

    try:
        fields = [parse_field_spec(s) for s in args.required]
    except ValueError as e:
        print(f"인자 오류: {e}")
        return 1

    try:
        with open(args.json_file, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"오류: 파일 없음 — {args.json_file}")
        return 1
    except json.JSONDecodeError as e:
        print(f"[결함] JSON 파싱 실패 — {args.json_file}: {e}")
        return 1

    try:
        records = find_records(data, args.records)
    except ValueError as e:
        print(f"오류: {e}")
        return 1

    if not records:
        print(f"[결함] 레코드 0건 — 빈 데이터는 통과가 아니다: {args.json_file}")
        return 1

    defects = []  # (index, record_id, message)
    for i, record in enumerate(records):
        rec_id = record.get("id", f"<index {i}>") if isinstance(record, dict) else f"<index {i}>"
        if not isinstance(record, dict):
            defects.append((i, rec_id, f"레코드가 객체가 아님 ({type_name(record)})"))
            continue
        for field, expected_type in fields:
            found, value = dig(record, field)
            if not found:
                defects.append((i, rec_id, f"필수 필드 누락: {field}"))
            elif value is None:
                defects.append((i, rec_id, f"필수 필드가 null: {field}"))
            elif expected_type is not None and not isinstance(value, expected_type):
                # bool은 int의 서브클래스 — int 기대 시 bool 오검출 방지
                if expected_type in (int, (int, float)) and isinstance(value, bool):
                    defects.append((i, rec_id, f"타입 불일치: {field} (기대 number, 실제 bool)"))
                else:
                    exp = (
                        expected_type.__name__
                        if isinstance(expected_type, type)
                        else "number"
                    )
                    defects.append(
                        (i, rec_id, f"타입 불일치: {field} (기대 {exp}, 실제 {type_name(value)})")
                    )

    print(f"검사: {args.json_file} — 레코드 {len(records)}건 × 필드 {len(fields)}개")

    if defects:
        print(f"\n[결함] {len(defects)}건:")
        for i, rec_id, msg in defects:
            print(f"  - 레코드 {i} (id={rec_id}): {msg}")
        return 1

    print("통과: 필수 필드 누락·타입 불일치 0건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
