"""
Lesson 1: How LLMs Actually Work Under the Hood (For Software Architects)
Author: Vishwanath S (@vishwanath_tns)

Instead of hiding behind heavy frameworks, this script shows the RAW HTTP JSON
contract of an Enterprise AI call:
1. System Instruction (The Architect's Rules)
2. User Payload (Unstructured Exchange FIX Gateway & Matching Engine Logs)
3. Temperature = 0.0 (Deterministic Mode for Backend Systems)
4. Response Schema (Forcing the LLM to output strict, parseable JSON)
"""

import json
import os
import urllib.request
import urllib.error


def build_llm_http_payload(raw_incident_log: str) -> dict:
    """
    Constructs the exact JSON payload sent over HTTPS to the LLM API.
    Notice how clean and familiar this is to any REST/Microservices Architect!
    """
    return {
        # 1. SYSTEM INSTRUCTION = Service-level configuration & role definition
        "system_instruction": {
            "parts": [
                {
                    "text": (
                        "You are an automated L3 Fintech Incident Triage Engine for a "
                        "low-latency Exchange Matching Engine and FIX Protocol Gateway. "
                        "Analyze raw error logs and return a deterministic JSON triage report."
                    )
                }
            ]
        },
        # 2. CONTENTS = The stateless request payload (the LLM has zero memory of past calls)
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"Analyze this production exchange log and extract root cause:\n\n{raw_incident_log}"
                    }
                ],
            }
        ],
        # 3. GENERATION CONFIG = Controlling determinism & enforcing a strict JSON Schema contract
        "generationConfig": {
            "temperature": 0.0,  # 0.0 = Maximum determinism (no "creative" hallucinations)
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "component": {
                        "type": "STRING",
                        "description": "Affected exchange subsystem (e.g., FIX_GATEWAY, MATCHING_ENGINE, REDIS_CACHE)",
                    },
                    "severity": {
                        "type": "STRING",
                        "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                    },
                    "rootCauseSummary": {
                        "type": "STRING",
                        "description": "Concise 1-sentence technical root cause",
                    },
                    "fixProtocolTagInvolved": {
                        "type": "INTEGER",
                        "description": "Relevant FIX tag number if applicable, or 0",
                    },
                    "recommendedAction": {
                        "type": "STRING",
                        "description": "Immediate deterministic mitigation step for the on-call engineer",
                    },
                },
                "required": [
                    "component",
                    "severity",
                    "rootCauseSummary",
                    "fixProtocolTagInvolved",
                    "recommendedAction",
                ],
            },
        },
    }


def call_gemini_api(payload: dict, api_key: str) -> dict:
    """Sends a raw HTTPS POST request to Google Gemini API (zero external libraries required)."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            structured_json_text = result["candidates"][0]["content"]["parts"][0]["text"]
            usage = result.get("usageMetadata", {})
            return {
                "mode": "LIVE_GEMINI_API",
                "parsed_output": json.loads(structured_json_text),
                "token_usage": {
                    "promptTokenCount": usage.get("promptTokenCount"),
                    "candidatesTokenCount": usage.get("candidatesTokenCount"),
                    "totalTokenCount": usage.get("totalTokenCount"),
                },
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"[Info] Live API returned HTTP {e.code} ({err_body[:160].strip()}...). Falling back to simulation:")
        return None


def main():
    # Sample messy production log from a FIX Gateway / Exchange Matching Engine
    sample_exchange_log = """
    2026-11-03 10:14:22.418 [WARN] [FIX-Session-Broker104] Incoming ExecutionReport (35=8) sequence gap detected.
    Expected MsgSeqNum(34)=14920, received 14925.
    2026-11-03 10:14:22.419 [ERROR] [Kafka-Order-Consumer-02] Redis position cache timeout ( > 50ms ) while validating
    Margin for AccountID=ICDX-8821 on OrderID=ORD-99102 (Symbol=GOLD-FUT, Side=1, OrdType=2, Price=2745.50).
    CircuitBreaker OPENED for Redis cluster shard-03. Order rejected with BusinessMessageReject (35=j, 380=0).
    """

    payload = build_llm_http_payload(sample_exchange_log)

    print("=" * 75)
    print("STEP 1: THE RAW HTTP PAYLOAD WE SEND TO THE LLM (STATELESS JSON CONTRACT)")
    print("=" * 75)
    print(json.dumps(payload, indent=2))

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    print("\n" + "=" * 75)
    result = None
    if api_key:
        print("STEP 2: CALLING LIVE GEMINI LLM API WITH TEMPERATURE=0.0 & JSON SCHEMA...")
        print("=" * 75)
        result = call_gemini_api(payload, api_key)

    if not result:
        if not api_key:
            print("STEP 2: SIMULATED LLM RESPONSE (Set $env:GEMINI_API_KEY for live API call)")
            print("=" * 75)
        result = {
            "mode": "SIMULATED_CONTRACT",
            "parsed_output": {
                "component": "REDIS_CACHE / FIX_GATEWAY",
                "severity": "CRITICAL",
                "rootCauseSummary": (
                    "Redis cluster shard-03 latency exceeded 50ms during margin validation "
                    "coupled with a FIX MsgSeqNum(34) gap (14920->14925) on Broker104, "
                    "tripping the circuit breaker and rejecting OrderID ORD-99102 (35=j)."
                ),
                "fixProtocolTagInvolved": 34,
                "recommendedAction": (
                    "1. Inspect Redis shard-03 CPU/network saturation and failover replica if needed. "
                    "2. Issue FIX ResendRequest (35=2) for sequence 14920-14924 on Session Broker104."
                ),
            },
            "token_usage": {
                "promptTokenCount": 248,
                "candidatesTokenCount": 96,
                "totalTokenCount": 344,
            },
        }

    print("\n[STRICT TYPED JSON RETURNED BY LLM - READY FOR KAFKA / MICROSERVICE]:")
    print(json.dumps(result["parsed_output"], indent=2))
    print("\n[TOKEN MEMORY USAGE (CONTEXT WINDOW COST)]:")
    print(json.dumps(result["token_usage"], indent=2))
    print("=" * 75)


if __name__ == "__main__":
    main()
