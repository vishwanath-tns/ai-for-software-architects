"""
Lesson 1: How LLMs Actually Work Under the Hood (For Software Architects)
Author: Vishwanath S (@vishwanath_tns)

Scenario Everyone Understands:
A customer sends a messy complaint message about a failed UPI payment on an online order.
Instead of getting a chatty English essay back from the AI, we use:
1. System Instruction (The AI's Role)
2. User Payload (The Customer's Messy Message)
3. Temperature = 0.0 (Zero Randomness / Deterministic Mode)
4. Response Schema (Forces the LLM to return strict JSON ready for our Backend/Database!)
"""

import json
import os
import urllib.request
import urllib.error


def build_llm_http_payload(customer_message: str) -> dict:
    """
    Constructs the exact JSON payload sent over HTTPS to the LLM API.
    """
    return {
        # 1. SYSTEM INSTRUCTION = Defines the AI's role & rules
        "system_instruction": {
            "parts": [
                {
                    "text": (
                        "You are an automated E-Commerce Support Ticket Analyzer. "
                        "Read raw customer messages and extract structured ticket data as strict JSON."
                    )
                }
            ]
        },
        # 2. CONTENTS = The raw input data we want the AI to analyze
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"Extract structured ticket details from this customer message:\n\n{customer_message}"
                    }
                ],
            }
        ],
        # 3. GENERATION CONFIG = Turn off randomness (0.0) & enforce a strict JSON Schema template
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "orderId": {
                        "type": "STRING",
                        "description": "The extracted Order ID (e.g., ORD-5582)",
                    },
                    "amountInr": {
                        "type": "INTEGER",
                        "description": "Transaction amount in INR",
                    },
                    "paymentMethod": {
                        "type": "STRING",
                        "enum": ["UPI", "CREDIT_CARD", "NET_BANKING", "COD", "UNKNOWN"],
                    },
                    "issueCategory": {
                        "type": "STRING",
                        "enum": [
                            "PAYMENT_DEDUCTED_ORDER_FAILED",
                            "LATE_DELIVERY",
                            "DAMAGED_PRODUCT",
                            "REFUND_REQUEST",
                        ],
                    },
                    "priority": {
                        "type": "STRING",
                        "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                    },
                    "assignToTeam": {
                        "type": "STRING",
                        "description": "Which backend queue or team should handle this ticket",
                    },
                },
                "required": [
                    "orderId",
                    "amountInr",
                    "paymentMethod",
                    "issueCategory",
                    "priority",
                    "assignToTeam",
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
        print(f"[Info] Live API returned HTTP {e.code}. Showing simulated output:")
        return None


def main():
    # A simple, everyday example anyone can understand: a messy customer complaint email
    sample_customer_message = """
    Hi Team, I ordered Sony Wireless Headphones (Order #ORD-5582) yesterday and paid Rs. 14999
    via UPI from my HDFC Bank account. The money was debited from my bank, but your app still
    shows 'Payment Failed' and my order is stuck! I have a flight tomorrow morning—please confirm
    my order or process an urgent refund immediately!
    """

    payload = build_llm_http_payload(sample_customer_message)

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
                "orderId": "ORD-5582",
                "amountInr": 14999,
                "paymentMethod": "UPI",
                "issueCategory": "PAYMENT_DEDUCTED_ORDER_FAILED",
                "priority": "CRITICAL",
                "assignToTeam": "PAYMENTS_RECONCILIATION_QUEUE",
            },
            "token_usage": {
                "promptTokenCount": 195,
                "candidatesTokenCount": 48,
                "totalTokenCount": 243,
            },
        }

    print("\n[STRICT TYPED JSON RETURNED BY LLM - READY FOR BACKEND / DATABASE]:")
    print(json.dumps(result["parsed_output"], indent=2))
    print("\n[TOKEN MEMORY USAGE (CONTEXT WINDOW COST)]:")
    print(json.dumps(result["token_usage"], indent=2))
    print("=" * 75)


if __name__ == "__main__":
    main()
