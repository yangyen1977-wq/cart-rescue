#!/usr/bin/env python3
"""
Ollama Cloud 多模型基準測試
測試目標：找出適合「即時異常判讀」的模型
測試項目：回應速度、結構化輸出、中文能力、電商語境理解
"""
import requests, json, time, os

API_KEY = os.getenv("OLLAMA_API_KEY", "42f3eb8bb692481e84b8a3a16408f4a3.gvtxpEXoVbj2CLFPT3LNHZwZ")
BASE_URL = "https://ollama.com/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 測試模型清單
MODELS = [
    {"name": "glm-5.3-flash", "reason": "Flash 版本 = 快速，智譜 GLM 系列中文強"},
    {"name": "deepseek-v4.1-flash", "reason": "Flash 版本，程式碼與推理能力強"},
    {"name": "nemotron-3-nano:30b", "reason": "僅 30B，輕量 = 快速"},
    {"name": "kimi-k3", "reason": "與 k2.6 對比，可能無 reasoning"},
    {"name": "mistral-large-4", "reason": "大型模型，品質基準"},
]

# 測試 Prompts
BASIC_PROMPT = "請用繁體中文自我介紹，20字以內。我是AI助理。"

ANOMALY_PROMPT = """你是電商審計AI。根據以下資訊判斷異常：
- 小計: NT$3,580
- 折扣: NT$0
- 總額: NT$3,580
- 預期: 折扣碼應折抵 NT$500
請只輸出：異常類型（如折扣失效）和信心分數（0-100），無需解釋。"""

def test_model(model_name, test_name, prompt, max_tokens=100):
    """測試單個模型單個任務"""
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.1
    }
    start = time.time()
    try:
        resp = requests.post(f"{BASE_URL}/chat/completions", headers=HEADERS, json=payload, timeout=60)
        elapsed = time.time() - start
        if resp.status_code != 200:
            return {
                "status": resp.status_code,
                "error": resp.text[:200],
                "elapsed": elapsed,
                "tokens": {}
            }
        data = resp.json()
        msg = data["choices"][0]["message"]
        content = msg.get("content", "")
        reasoning = msg.get("reasoning", "")
        tokens = data.get("usage", {})
        return {
            "status": 200,
            "elapsed": elapsed,
            "content": content[:300] if content else "(empty)",
            "reasoning": reasoning[:200] if reasoning else "(empty)",
            "tokens": tokens,
            "finish_reason": data["choices"][0].get("finish_reason", "")
        }
    except Exception as e:
        elapsed = time.time() - start
        return {"status": "error", "error": str(e)[:200], "elapsed": elapsed}

def main():
    print("=" * 70)
    print("Ollama Cloud 多模型基準測試")
    print(f"時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    results = []
    
    for model in MODELS:
        name = model["name"]
        reason = model["reason"]
        print(f"\n{'─' * 70}")
        print(f"模型: {name}")
        print(f"預期特性: {reason}")
        print(f"{'─' * 70}")
        
        # 測試 1: 基本對話
        r1 = test_model(name, "basic", BASIC_PROMPT, max_tokens=80)
        print(f"  [基本對話] {r1['elapsed']:.2f}s | content: {r1.get('content','')[:60]}...")
        
        # 測試 2: 異常判讀
        r2 = test_model(name, "anomaly", ANOMALY_PROMPT, max_tokens=150)
        print(f"  [異常判讀] {r2['elapsed']:.2f}s | content: {r2.get('content','')[:80]}...")
        
        results.append({
            "model": name,
            "reason": reason,
            "basic": r1,
            "anomaly": r2
        })
    
    # 彙總表格
    print(f"\n{'=' * 70}")
    print("彙總比較表")
    print(f"{'=' * 70}")
    print(f"{'模型':<25s} | {'對話時間':<8s} | {'異常時間':<8s} | {'對話內容':<20s} | {'異常輸出':<25s}")
    print(f"{'-'*25}-+-{'-'*8}-+-{'-'*8}-+-{'-'*20}-+-{'-'*25}")
    
    for r in results:
        name = r["model"]
        b = r["basic"]
        a = r["anomaly"]
        b_time = f"{b['elapsed']:.1f}s" if b.get("status") == 200 else f"ERR({b.get('status','X')})"
        a_time = f"{a['elapsed']:.1f}s" if a.get("status") == 200 else f"ERR({a.get('status','X')})"
        b_content = b.get("content", "")[:18] + "..." if len(b.get("content","")) > 18 else b.get("content", "N/A")
        a_content = a.get("content", "")[:23] + "..." if len(a.get("content","")) > 23 else a.get("content", "N/A")
        print(f"{name:<25s} | {b_time:>8s} | {a_time:>8s} | {b_content:<20s} | {a_content:<25s}")
    
    # 儲存結果
    output_path = "/home/cartrescue/CartRescue_AI/research/MULTI_MODEL_BASELINE.json"
    with open(output_path, "w") as f:
        json.dump({
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "total_models_tested": len(MODELS),
            "results": results
        }, f, indent=2, ensure_ascii=False)
    print(f"\n結果已儲存至: {output_path}")

if __name__ == "__main__":
    main()
