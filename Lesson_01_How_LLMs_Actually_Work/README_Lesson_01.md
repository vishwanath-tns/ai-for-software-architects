# Lesson 01: Under the Hood of an LLM (Why Backend Code Can't Use "Chatty" AI)

**By Vishwanath S** | [@vishwanath_tns](https://x.com/vishwanath_tns)

---

## 1. The Everyday Problem We Are Solving

Imagine a customer orders **Sony Wireless Headphones (`Order #ORD-5582`)** on your app, pays **₹14,999 via UPI**, and sends an angry support message because the money was debited from their bank, but your app still shows *"Payment Failed"*.

* **If you send that message to normal ChatGPT:** It replies with a polite 3-paragraph English essay (*"I am so sorry to hear about your headphones..."*).
* **The Backend Problem:** Your Java microservice, SQL database, or Kafka pipeline **cannot parse an English essay!** It needs a clean, predictable JSON object.

---

## 2. How Architects Solve This: Raw HTTP + `temperature=0.0` + `responseSchema`

When you strip away heavy frameworks, calling an LLM API is just a **stateless HTTP `POST` request** containing **3 instructions**:

| JSON Field | What It Does | Systems Architecture Equivalent |
| :--- | :--- | :--- |
| **`1. system_instruction`** | *"You are an automated E-Commerce Ticket Analyzer."* | **Microservice Configuration** |
| **`2. contents`** | The customer's raw unstructured complaint message | **Stateless Request Payload** |
| **`3. generationConfig`** | Sets `temperature: 0.0` (zero randomness) + `responseSchema` | **Strict OpenAPI / JSON Schema Contract** |

---

## 3. Run the Code (`lesson1_architect_ai_demo.py`)

This script uses **pure Python 3.11+ standard library** (`urllib.request` + `json`—zero `pip install` needed!).

```bash
# Run in Simulation Mode (inspects the exact HTTP JSON payload & output immediately)
python Lesson_01_How_LLMs_Actually_Work/lesson1_architect_ai_demo.py

# Or run against the Live Google Gemini API (Free API key: https://aistudio.google.com/apikey)
$env:GEMINI_API_KEY="your_api_key_here"
python Lesson_01_How_LLMs_Actually_Work/lesson1_architect_ai_demo.py
```

### Output Returned by the LLM (100% Pure JSON):
```json
{
  "orderId": "ORD-5582",
  "amountInr": 14999,
  "paymentMethod": "UPI",
  "issueCategory": "PAYMENT_DEDUCTED_ORDER_FAILED",
  "priority": "CRITICAL",
  "assignToTeam": "PAYMENTS_RECONCILIATION_QUEUE"
}
```
