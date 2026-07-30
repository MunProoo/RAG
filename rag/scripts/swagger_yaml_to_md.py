"""
swagger_kr.yaml → Markdown (RAG/벡터 검색용)

사용법 (rag/ 디렉터리에서):
  python scripts/swagger_yaml_to_md.py
  python scripts/swagger_yaml_to_md.py --input ./data/docs/swagger_kr.yaml --output ./data/docs/swagger_kr.md
"""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

HTTP_METHODS = ("get", "post", "put", "delete", "patch", "head", "options")


def _esc_cell(s: str, max_len: int = 400) -> str:
    if s is None:
        return ""
    t = str(s).replace("\r\n", "\n").replace("\n", " ").replace("|", "\\|").strip()
    if len(t) > max_len:
        t = t[: max_len - 1] + "…"
    return t


def _ref_name(ref: str) -> str:
    if not ref or not isinstance(ref, str):
        return ""
    if ref.startswith("#/definitions/"):
        return ref.split("/")[-1]
    return ref


def _schema_type(spec: Dict[str, Any]) -> str:
    if not isinstance(spec, dict):
        return ""
    if "$ref" in spec:
        return _ref_name(spec["$ref"])
    t = spec.get("type", "")
    items = spec.get("items")
    if t == "array" and isinstance(items, dict):
        it = items.get("$ref")
        if it:
            return f"array<{_ref_name(it)}>"
        return f"array<{items.get('type', '')}>"
    return str(t)


def _direct_refs(spec: Any) -> List[str]:
    """스키마 사양에서 곧바로 참조하는 정의 이름을 반환합니다."""
    refs: List[str] = []
    if isinstance(spec, dict):
        if spec.get("$ref"):
            refs.append(_ref_name(spec["$ref"]))
        items = spec.get("items")
        if isinstance(items, dict) and items.get("$ref"):
            refs.append(_ref_name(items["$ref"]))
    return refs


def collect_operation_schema_refs(
    op: Dict[str, Any],
    params: List[Dict[str, Any]],
    defs: Dict[str, Any],
    max_depth: int = 2,
) -> List[str]:
    """엔드포인트의 파라미터/응답이 참조하는 스키마 이름을 중첩 참조까지 수집합니다.

    API 상세와 스키마 정의는 원문에서 멀리 떨어져 있어 서로 다른 청크로 쪼개집니다.
    각 엔드포인트 섹션 안에 스키마를 함께 실어야(자기완결 청크) 한 번의 검색으로
    요청/응답 구조까지 답할 수 있습니다.
    """
    ordered: List[str] = []

    def visit(name: str, depth: int) -> None:
        if not name or name in ordered or name not in defs or depth > max_depth:
            return
        ordered.append(name)
        schema = defs.get(name)
        if not isinstance(schema, dict):
            return
        for spec in (schema.get("properties") or {}).values():
            for child in _direct_refs(spec):
                visit(child, depth + 1)

    roots: List[str] = []
    for p in params:
        if isinstance(p, dict):
            roots.extend(_direct_refs(p.get("schema")))
    for r in (op.get("responses") or {}).values():
        if isinstance(r, dict):
            roots.extend(_direct_refs(r.get("schema")))
    for root in roots:
        visit(root, 1)
    return ordered


def emit_schema_fields_table(schema: Any, lines: List[str]) -> None:
    """스키마 필드 표를 출력합니다 (정의 섹션·엔드포인트 인라인 공용)."""
    if not isinstance(schema, dict):
        return
    if schema.get("description"):
        lines.append(str(schema.get("description", "")))
        lines.append("")
    props = schema.get("properties")
    if isinstance(props, dict) and props:
        lines.append("| 필드 | 타입 | 필수 | 설명 |")
        lines.append("|------|------|------|------|")
        req_set = set(schema.get("required") or [])
        for prop, spec in props.items():
            if not isinstance(spec, dict):
                continue
            typ = _esc_cell(_schema_type(spec))
            desc = _esc_cell(spec.get("description", ""))
            rq = "예" if prop in req_set else ""
            lines.append(f"| `{_esc_cell(prop)}` | {typ} | {rq} | {desc} |")
    else:
        lines.append(f"- **type**: `{schema.get('type', '')}`")


def emit_info_md(data: Dict[str, Any], lines: List[str]) -> None:
    info = data.get("info") or {}
    lines.append("# Alpeta Server Web API (Swagger 2.0 → Markdown)")
    lines.append("")
    lines.append("벡터 검색·RAG용으로 `swagger_kr.yaml`을 마크다운으로 변환한 문서입니다.")
    lines.append("")
    lines.append(f"- **title**: {info.get('title', '')}")
    lines.append(f"- **version**: {info.get('version', '')}")
    if info.get("description"):
        lines.append(f"- **description**: {info.get('description', '')}")
    host = data.get("host") or ""
    base = data.get("basePath") or ""
    schemes = data.get("schemes") or ["http"]
    scheme = schemes[0] if schemes else "http"
    if host:
        lines.append(f"- **Base URL**: `{scheme}://{host}{base}`")
    else:
        lines.append(f"- **basePath**: `{base}`")
    lines.append("")


def emit_tags_table(tags: Any, lines: List[str]) -> None:
    if not tags:
        return
    lines.append("## API 태그 목록")
    lines.append("")
    lines.append("| 태그 | 설명 |")
    lines.append("|------|------|")
    for t in tags:
        if not isinstance(t, dict):
            continue
        name = _esc_cell(t.get("name", ""))
        desc = _esc_cell(t.get("description", ""))
        lines.append(f"| `{name}` | {desc} |")
    lines.append("")


def emit_paths_md(data: Dict[str, Any], lines: List[str]) -> None:
    paths = data.get("paths") or {}
    base = data.get("basePath") or ""
    defs = data.get("definitions") or {}

    for path_item in sorted(paths.keys()):
        path_obj = paths[path_item]
        if not isinstance(path_obj, dict):
            continue
        path_level_params = path_obj.get("parameters") or []

        for method in HTTP_METHODS:
            op = path_obj.get(method)
            if not isinstance(op, dict):
                continue
            method_u = method.upper()
            full_path = f"{base}{path_item}" if base else path_item
            lines.append(f"## {method_u} `{full_path}`")
            lines.append("")
            if op.get("summary"):
                lines.append(f"- **요약**: {op.get('summary', '')}")
            if op.get("description"):
                d = textwrap.dedent(str(op.get("description", ""))).strip()
                if d:
                    lines.append(f"- **설명**: {d}")
            if op.get("tags"):
                lines.append(f"- **태그**: {', '.join(str(x) for x in op['tags'])}")
            if op.get("deprecated"):
                lines.append("- **deprecated**: true")
            consumes = op.get("consumes") or []
            produces = op.get("produces") or []
            if consumes:
                lines.append(f"- **consumes**: `{', '.join(consumes)}`")
            if produces:
                lines.append(f"- **produces**: `{', '.join(produces)}`")

            params: List[Dict[str, Any]] = []
            for p in path_level_params:
                if isinstance(p, dict):
                    params.append(p)
            for p in op.get("parameters") or []:
                if isinstance(p, dict):
                    params.append(p)

            if params:
                lines.append("")
                lines.append("**파라미터**")
                lines.append("| 이름 | 위치 | 필수 | 타입 | 설명 |")
                lines.append("|------|------|------|------|------|")
                for p in params:
                    nm = _esc_cell(p.get("name", ""))
                    loc = _esc_cell(p.get("in", ""))
                    req = "예" if p.get("required") else "아니오"
                    sch = p.get("schema")
                    if isinstance(sch, dict) and sch.get("$ref"):
                        typ = _ref_name(sch["$ref"])
                    else:
                        typ = _esc_cell(p.get("type", "") or _schema_type(sch) if isinstance(sch, dict) else "")
                    desc = _esc_cell(p.get("description", ""))
                    lines.append(f"| `{nm}` | {loc} | {req} | {typ} | {desc} |")

            responses = op.get("responses") or {}
            if responses:
                lines.append("")
                lines.append("**응답**")
                lines.append("| 코드 | 설명 | 스키마 |")
                lines.append("|------|------|--------|")
                for code in sorted(responses.keys(), key=lambda x: str(x)):
                    r = responses[code]
                    if not isinstance(r, dict):
                        lines.append(f"| `{code}` | | |")
                        continue
                    desc = _esc_cell(r.get("description", ""))
                    sch = r.get("schema")
                    ref = ""
                    if isinstance(sch, dict) and sch.get("$ref"):
                        ref = "`" + _ref_name(sch["$ref"]) + "`"
                    lines.append(f"| `{code}` | {desc} | {ref} |")

            # `###` 헤딩을 쓰면 인덱서가 스키마를 별도 청크로 분리해 버리므로
            # 굵은 텍스트로 같은 엔드포인트 섹션 안에 유지합니다.
            for schema_name in collect_operation_schema_refs(op, params, defs):
                lines.append("")
                lines.append(f"**스키마 `{schema_name}`** (이 API의 요청/응답 구조)")
                lines.append("")
                emit_schema_fields_table(defs.get(schema_name), lines)

            lines.append("")
            lines.append("---")
            lines.append("")


def emit_definitions_md(data: Dict[str, Any], lines: List[str]) -> None:
    defs = data.get("definitions") or {}
    if not defs:
        return
    lines.append("## 스키마 정의 (definitions)")
    lines.append("")
    lines.append("아래는 모델/응답 구조입니다. API 경로 검색과 함께 참고하세요.")
    lines.append("")

    for name in sorted(defs.keys()):
        schema = defs[name]
        lines.append(f"### 스키마 `{name}`")
        lines.append("")
        if not isinstance(schema, dict):
            lines.append("")
            continue
        emit_schema_fields_table(schema, lines)
        lines.append("")
        lines.append("---")
        lines.append("")


def convert(input_path: Path, output_path: Path) -> None:
    raw = yaml.safe_load(input_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit("YAML root must be mapping")

    lines: List[str] = []
    emit_info_md(raw, lines)
    emit_tags_table(raw.get("tags"), lines)
    emit_paths_md(raw, lines)
    emit_definitions_md(raw, lines)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {output_path} ({output_path.stat().st_size // 1024} KB)")


def main() -> None:
    here = Path(__file__).resolve().parent
    rag_root = here.parent
    default_in = rag_root / "data" / "docs" / "swagger_kr.yaml"
    default_out = rag_root / "data" / "docs" / "swagger_kr.md"

    ap = argparse.ArgumentParser(description="Swagger 2.0 YAML → Markdown")
    ap.add_argument("--input", type=Path, default=default_in)
    ap.add_argument("--output", type=Path, default=default_out)
    args = ap.parse_args()

    if not args.input.exists():
        raise SystemExit(f"입력 없음: {args.input}")

    convert(args.input, args.output)


if __name__ == "__main__":
    main()
