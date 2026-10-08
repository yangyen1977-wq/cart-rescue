#!/usr/bin/env python3
"""
Ollama Cloud API (kimi-k2.6) 基準測試腳本 v2
修正：kimi-k2.6 在 Ollama Cloud 上啟用 reasoning，輸出在 reasoning 欄位
"""
import requests, json, time, os

API_KEY = os.getenv("OLLAMA_API_KEY", "42f3eb8bb692481e84b8a3a16408f4a3.gvtxpEXoVbj2CLFPT3LNHZwZ")
BASE_URL = "https://ollama.com/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def chat(messages, max_tokens=500, temperature=0.3):
    payload = {
        "model": "kimi-k2.6",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    start = time.time()
    resp = requests.post(f"{BASE_URL}/chat/completions", headers=HEADERS, json=payload, timeout=120)
    elapsed = time.time() - start
    return resp, elapsed

def extract_output(data):
    """kimi-k2.6 在 Ollama Cloud 輸出在 reasoning 欄位"""
    msg = data["choices"][0]["message"]
    content = msg.get("content", "")
    reasoning = msg.get("reasoning", "")
    return content.strip(), reasoning.strip(), msg.get("role", "")

def test_basic_chat():
    print("=" * 60)
    print("測試 1: 基本對話（繁體中文）")
    print("=" * 60)
    resp, elapsed = chat([{"role": "user", "content": "請用繁體中文自我介紹，50字以內。我是AI助理。"}], max_tokens=150)
    data = resp.json()
    content, reasoning, role = extract_output(data)
    tokens = data.get("usage", {})
    print(f"Status:          {resp.status_code}")
    print(f"Prompt tokens:   {tokens.get('prompt_tokens', 'N/A')}")
    print(f"Completion:      {tokens.get('completion_tokens', 'N/A')}")
    print(f"Total tokens:    {tokens.get('total_tokens', 'N/A')}")
    print(f"回應時間:        {elapsed:.2f}s")
    print(f"content:         {content[:100] if content else '(empty)'}")
    print(f"reasoning:       {reasoning[:300] if reasoning else '(empty)'}")
    print()
    return {"test": "basic", "elapsed": elapsed, "tokens": tokens, "content_preview": content[:100], "reasoning_preview": reasoning[:200]}

def test_anomaly_judgment():
    print("=" * 60)
    print("測試 2: 模擬異常判讀（折扣碼失效）")
    print("=" * 60)
    prompt = """你是一個電商結帳審計 AI。請根據以下資訊判斷是否有異常，並用 JSON 回應。

【頁面資訊】
- URL: https://travelplus.com.tw/checkout
- 步驟: 輸入折扣碼後點擊「應用」
- 頁面文字: "此折扣碼不適用於您的購物車"
- 小計: NT$3,580
- 折扣: NT$0
- 總額: NT$3,580
- 預期: 折扣碼「SUMMER20」應折抵 NT$500

請輸出:
{
  "anomaly_detected": true/false,
  "type": "類型代碼",
  "severity": "critical/warning/info",
  "confidence": 0-100,
  "description": "異常描述（繁體中文）",
  "fix": "修復建議"
}"""
    resp, elapsed = chat([{"role": "user", "content": prompt}], max_tokens=400, temperature=0.1)
    data = resp.json()
    content, reasoning, role = extract_output(data)
    tokens = data.get("usage", {})
    print(f"Status:          {resp.status_code}")
    print(f"Prompt tokens:   {tokens.get('prompt_tokens', 'N/A')}")
    print(f"Completion:      {tokens.get('completion_tokens', 'N/A')}")
    print(f"回應時間:        {elapsed:.2f}s")
    print(f"content:         {content[:200] if content else '(empty)'}")
    print(f"reasoning:       {reasoning[:400] if reasoning else '(empty)'}")
    print()
    return {"test": "anomaly", "elapsed": elapsed, "tokens": tokens, "content_preview": content[:200], "reasoning_preview": reasoning[:300]}

def test_code_generation():
    print("=" * 60)
    print("測試 3: Python 程式碼生成（規則引擎）")
    print("=" * 60)
    prompt = """用 Python 寫函數 `check_discount(subtotal, discount, total)`，檢查折扣計算。
錯誤時回傳錯誤訊息（繁體中文），正確回傳 None。
只需函數本體。"""
    resp, elapsed = chat([{"role": "user", "content": prompt}], max_tokens=250, temperature=0.1)
    data = resp.json()
    content, reasoning, role = extract_output(data)
    tokens = data.get("usage", {})
    print(f"Status:          {resp.status_code}")
    print(f"Prompt tokens:   {tokens.get('prompt_tokens', 'N/A')}")
    print(f"Completion:      {tokens.get('completion_tokens', 'N/A')}")
    print(f"回應時間:        {elapsed:.2f}s")
    print(f"content:         {content[:200] if content else '(empty)'}")
    print(f"reasoning:       {reasoning[:400] if reasoning else '(empty)'}")
    print()
    return {"test": "code", "elapsed": elapsed, "tokens": tokens, "content_preview": content[:200], "reasoning_preview": reasoning[:300]}

def main():
    print("Ollama Cloud API (kimi-k2.6) 基準測試 v2")
    print(f"API Endpoint: {BASE_URL}")
    print(f"時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("注意: kimi-k2.6 啟用 reasoning 模式，輸出在 'reasoning' 欄位")
    print()
    
    results = []
    results.append(test_basic_chat())
    results.append(test_anomaly_judgment())
    results.append(test_code_generation())
    
    print("=" * 60)
    print("彙總")
    print("=" * 60)
    total_time = sum(r["elapsed"] for r in results)
    for r in results:
        print(f"{r['test']:15s} | {r['elapsed']:5.2f}s | {r['tokens'].get('total_tokens', 'N/A')} tokens")
    print(f"{'TOTAL':15s} | {total_time:5.2f}s")
    
    output_path = "/home/cartrescue/CartRescue_AI/research/OLLAMA_BASELINE_TEST_V2.json"
    with open(output_path, "w") as f:
        json.dump({"timestamp": time.strftime('%Y-%m-%d %H:%M:%S'), "model": "kimi-k2.6", "notes": "Outputs in reasoning field", "results": results}, f, indent=2, ensure_ascii=False)
    print(f"\n結果已儲存至: {output_path}")

if __name__ == "__main__":
    main()
