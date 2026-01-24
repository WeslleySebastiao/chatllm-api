from typing import Any

def normalize_line_range(lr: Any) -> str:
    if lr is None:
        return ""
    if isinstance(lr, str):
        return lr
    if isinstance(lr, list) and lr:
        if len(lr) == 1:
            return str(lr[0])
        return f"{lr[0]}-{lr[-1]}"
    return ""

def normalize_findings(findings: list[dict]) -> list[dict]:
    out = []
    for f in findings or []:
        f2 = dict(f)
        f2["line_range"] = normalize_line_range(f2.get("line_range"))
        # defaults úteis
        f2.setdefault("confidence", None)
        f2.setdefault("source_agent", None)
        out.append(f2)
    return out
