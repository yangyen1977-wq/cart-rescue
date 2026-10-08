#!/usr/bin/env python3
"""
Ollama Cloud API (kimi-k2.6) 基準測試腳本
測試項目：回應速度、中文能力、模擬異常判讀
"""
import requests, json, time, os

API_KEY = os.getenv("OLLAMA_API_KEY", "42f3eb8bb692481e84b8a3a16408f4a3.gvtxpEXoVbj2CLFPT3LNHZwZ")
BASE_URL = "https://ollama.com/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def chat(messages, max_tokens=500, temperature=0.3):
    """發送 chat completion 請求"""
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

def test_basic_chat():
    """測試 1: 基本對話與速度"""
    print("=" * 60)
    print("測試 1: 基本對話（中文）")
    print("=" * 60)
    resp, elapsed = chat([{"role": "user", "content": "請用繁體中文自我介紹，50字以內。"}], max_tokens=100)
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {})
    print(f"Prompt tokens:   {tokens.get('prompt_tokens', 'N/A')}")
    print(f"Completion tokens: {tokens.get('completion_tokens', 'N/A')}")
    print(f"Total tokens:    {tokens.get('total_tokens', 'N/A')}")
    print(f"回應時間:        {elapsed:.2f}s")
    print(f"模型輸出:\n{content.strip()}")
    print()
    return {"test": "basic", "elapsed": elapsed, "tokens": tokens}

def test_anomaly_judgment():
    """測試 2: 模擬異常判讀（網頁截圖描述）"""
    print("=" * 60)
    print("測試 2: 模擬異常判讀（折扣碼失效情境）")
    print("=" * 60)
    prompt = """你是一個電商結帳審計 AI。以下是一次巡檢的頁面資訊，請判斷是否有異常。

【頁面資訊】
- URL: https://travelplus.com.tw/checkout
- 步驟: 輸入折扣碼後點擊「應用」
- 頁面文字: "此折扣碼不適用於您的購物車"
- 小計: NT$3,580
- 折扣: NT$0
- 總額: NT$3,580
- 預期: 折扣碼「SUMMER20」應折抵 NT$500

請輸出 JSON:
{
  "anomaly_detected": true/false,
  "anomaly_type": "類型",
  "severity": "critical/warning/info",
  "confidence": 0-100,
  "description": "異常描述（繁體中文）",
  "suggested_fix": "修復建議"
}"""
    resp, elapsed = chat([{"role": "user", "content": prompt}], max_tokens=300, temperature=0.1)
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {})
    print(f"Prompt tokens:   {tokens.get('prompt_tokens', 'N/A')}")
    print(f"Completion tokens: {tokens.get('completion_tokens', 'N/A')}")
    print(f"回應時間:        {elapsed:.2f}s")
    print(f"模型輸出:\n{content.strip()}")
    print()
    return {"test": "anomaly", "elapsed": elapsed, "tokens": tokens}

def test_code_generation():
    """測試 3: 程式碼生成（規則引擎片段）"""
    print("=" * 60)
    print("測試 3: Python 程式碼生成（規則引擎）")
    print("=" * 60)
    prompt = """請用 Python 寫一個函數 `check_discount_invariant(subtotal, discount_amount, total)`，
檢查折扣計算是否正確。若錯誤則回傳錯誤訊息（繁體中文），正確則回傳 None。
只需函數本體，不要範例。"""
    resp, elapsed = chat([{"role": "user", "content": prompt}], max_tokens=200, temperature=0.1)
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {})
    print(f"Prompt tokens:   {tokens.get('prompt_tokens', 'N/A')}")
    print(f"Completion tokens: {tokens.get('completion_tokens', 'N/A')}")
    print(f"回應時間:        {elapsed:.2f}s")
    print(f"模型輸出:\n{content.strip()}")
    print()
    return {"test": "code", "elapsed": elapsed, "tokens": tokens}

def main():
    print("Ollama Cloud API (kimi-k2.6) 基準測試")
    print(f"API Endpoint: {BASE_URL}")
    print(f"時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    results.append(test_basic_chat())
    results.append(test_anomaly_judgment())
    results.append(test_code_generation())
    
    # 彙總
    print("=" * 60)
    print("彙總")
    print("=" * 60)
    total_time = sum(r["elapsed"] for r in results)
    for r in results:
        print(f"{r['test']:15s} | {r['elapsed']:.2f}s | {r['tokens'].get('total_tokens', 'N/A')} tokens")
    print(f"{'TOTAL':15s} | {total_time:.2f}s")
    
    # 儲存結果
    os.makedirs("/home/cartrescue/CartRescue_AI/research", exist_ok=True)
    with open("/home/cartrescue/CartRescue_AI/research/OLLAMA_BASELINE_TEST.json", "w") as f:
        json.dump({"timestamp": time.strftime('%Y-%m-%d %H:%M:%S'), "results": results}, f, indent=2, ensure_ascii=False)
    print(f"\n結果已儲存至: research/OLLAMA_BASELINE_TEST.json")

if __name__ == "__main__":
    main()
