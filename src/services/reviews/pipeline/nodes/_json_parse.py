import json
import re

def safe_parse_json(text: str) -> dict:
    if not text:
        return _build_error("Empty input")

    # Tenta parsear direto primeiro (caso ideal)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # ESTRATÉGIA ROBUSTA: Encontrar o JSON delimitado
    # Procura desde o primeiro '{' até o último '}'
    # O flag DOTALL permite que o ponto (.) case com quebras de linha
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    
    if match:
        json_candidate = match.group(1).strip()
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError:
            # Se falhar aqui, o JSON interno pode estar malformado
            pass
    
    # Se chegou aqui, falhou totalmente
    return _build_error(f"Failed to parse JSON. Raw content prefix: {text[:200]}")

def _build_error(msg: str) -> dict:
    return {
        "agent": "parse_error",
        "findings": [{
            "severity": "MAJOR",
            "title": "JSON Parse Error",
            "file": "",
            "line_range": "",
            "evidence": msg,
            "recommendation": "Check model output format.",
            "confidence": 1.0
        }],
        "tests_suggested": []
    }