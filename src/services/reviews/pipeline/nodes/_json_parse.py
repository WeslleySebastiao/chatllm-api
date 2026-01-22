import json
import re

def safe_parse_json(text: str) -> dict:
    if not text:
        return {
            "agent": "parse_error",
            "findings": [{
                "severity": "MAJOR",
                "title": "Empty agent output",
                "file": "",
                "line_range": "",
                "evidence": "Model returned empty string",
                "recommendation": "Verificar logs do runtime e prompt.",
                "confidence": 1.0
            }],
            "tests_suggested": []
        }

    cleaned = text.strip()

    # Remove fences ```json ... ``` ou ``` ... ```
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    # Se ainda tiver texto extra, tenta extrair o primeiro objeto JSON { ... }
    if not cleaned.startswith("{"):
        m = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if m:
            cleaned = m.group(0).strip()

    try:
        return json.loads(cleaned)
    except Exception as e:
        return {
            "agent": "parse_error",
            "findings": [{
                "severity": "MAJOR",
                "title": "Agent output is not valid JSON",
                "file": "",
                "line_range": "",
                "evidence": f"JSON parse error: {e}. Output prefix: {text[:200]}",
                "recommendation": "Ajustar prompt do agente para retornar SOMENTE JSON válido e sem markdown.",
                "confidence": 1.0
            }],
            "tests_suggested": []
        }
