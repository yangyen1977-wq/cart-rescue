# TravelPlus 模型每日測試報告 Day 21（2026-10-08）

## 當日測試模型

| 模型 | 類型 | 測試項目 | 狀態 |
|------|------|---------|------|
| **GPT-4o-mini（OpenAI）** | 導航 | 網站結構分析、結帳流程規劃 | ❌ 未執行 |
| **Gemini 2.0 Flash（Google）** | 導航 | 產品價格比對、折扣計算 | ❌ 未執行 |

> **未執行原因**：系統環境中未發現任何 API 金鑰（OLLAMA_API_KEY、OPENAI_API_KEY、OPENROUTER_API_KEY、KIMI_API_KEY、ANTHROPIC_API_KEY 等均不存在）。無法呼叫任何外部 LLM API。

---

## 一、網站結構分析（travelplus.com.tw）

### 1.1 首頁掃描（Browser 實測）

| 項目 | 結果 |
|------|------|
| 網站標題 | 🐴 t+樂遊家戶外旅遊專賣店 首頁 |
| HTML 總連結數 | **815**（較前次 319 大幅增加，反映首頁動態載入更多內容） |
| 首頁商品數 | **150 件**（AZPAC 行李箱系列為主打） |
| 分類結構 | 出國旅行 → 行李箱/防搶系列/旅用配件/打理包/旅行衣物 |

**導航結構確認**：
- 一級分類：出國旅行、背包、男性服飾、女性服飾、鞋子
- 二級分類（行李箱）：cid=436（行李箱）、cid=437（防搶系列）、cid=420（旅用配件）
- 會員功能：登入、會員價顯示、前往結帳
- 產品頁格式：`product.aspx?ProductColorProductID={ID}`

### 1.2 行李箱分類頁（cid=436）批次擷取

使用瀏覽器 DOM 提取 + curl 驗證，成功取得 **15 筆產品價格**（SSR 網站，HTML 含完整價格資訊）：

| # | 產品名稱 | 定價 | 會員價 | 實際折扣 |
|---|---------|------|--------|---------|
| 1 | AZPAC 30吋 Trucker 3.0 防爆煞車行李箱 | NT$12,800 | NT$8,280 | **6.5 折** |
| 2 | AZPAC 30吋 Trucker 3.0 前開行李箱 7:3半開 | NT$15,800 | NT$9,080 | **5.7 折** |
| 3 | AZPAC 30吋 Trucker 3.0 防爆煞車行李箱 | NT$12,800 | NT$8,280 | **6.5 折** |
| 4 | AZPAC 30吋 Trucker 3.0 前開行李箱 7:3半開 | NT$15,800 | NT$9,080 | **5.7 折** |
| 5 | AZPAC 26吋 Trucker 3.0 防爆煞車行李箱 | NT$11,800 | NT$7,280 | **6.2 折** |
| 6 | AZPAC 26吋 Trucker 3.0 前開行李箱 7:3半開 | NT$13,800 | NT$8,080 | **5.9 折** |
| 7 | AZPAC 26吋 Trucker 3.0 防爆煞車行李箱 | NT$11,800 | NT$7,280 | **6.2 折** |
| 8 | AZPAC 30吋 Trucker 3.0 防爆煞車行李箱 | NT$12,800 | NT$8,280 | **6.5 折** |
| 9 | AZPAC 30吋 Trucker 3.0 防爆煞車行李箱 | NT$12,800 | NT$8,280 | **6.5 折** |
| 10 | AZPAC 30吋 Trucker 3.0 防爆煞車行李箱 | NT$12,800 | NT$8,280 | **6.5 折** |
| 11 | AZPAC 20吋 Trucker 3.0 前開行李箱 登機箱 | NT$8,800 | NT$6,400 | **7.3 折** |
| 12 | AZPAC 20吋 Trucker 3.0 前開行李箱 登機箱 | NT$8,800 | NT$6,400 | **7.3 折** |
| 13 | AZPAC 26吋 Trucker 3.0 前開行李箱 7:3半開 | NT$13,800 | NT$8,080 | **5.9 折** |
| 14 | AZPAC 30吋 Trucker 3.0 前開行李箱 7:3半開 | NT$15,800 | NT$9,080 | **5.7 折** |
| 15 | AZPAC 30吋 Trucker 3.0 前開行李箱 7:3半開 | NT$15,800 | NT$9,080 | **5.7 折** |

> **觀察**：TravelPlus 所有產品均顯示「定價」與「會員價」，**無標示折扣百分比**。這是 CartRescue 審計的經典情境——消費者無法直觀判斷折扣力度，需要 LLM 幫忙計算實際折扣率。

### 1.3 產品頁面分析

嘗試訪問單一產品頁（Product.aspx），但連結被導回產品列表頁。網站可能採用：
- 點擊產品後在新分頁開啟（target="_blank"）
- 或需登入才能查看完整產品詳情

**對 CartRescue 的影響**：
- 列表頁已含足夠價格資訊（定價 + 會員價）
- 無需深入產品頁即可完成「折扣率審計」
- 但「結帳流程審計」仍需模擬加入購物車 → 結帳的完整路徑

---

## 二、模型測試結果

### ⚠️ 今日無法進行模型測試

**原因**：系統環境中未配置任何 LLM API 金鑰。檢查結果：

| 金鑰 | 狀態 |
|------|------|
| OLLAMA_API_KEY | ❌ 不存在 |
| OPENAI_API_KEY | ❌ 不存在 |
| OPENROUTER_API_KEY | ❌ 不存在 |
| KIMI_API_KEY | ❌ 不存在 |
| DEEPSEEK_API_KEY | ❌ 不存在 |
| ANTHROPIC_API_KEY | ❌ 不存在 |

**歷史參照**：Day 1–20 的測試透過 Ollama Cloud（`https://ollama.com/v1`）的 `OLLAMA_API_KEY` 進行。該金鑰似乎僅在特定 session 中可用，cron job 執行時未載入。

**建議**：
1. 將 API 金鑰寫入 cron job 的環境變數（`~/.hermes/cron/` 或系統級 env）
2. 或改用不需要金鑰的本地模型（如 llama.cpp + GGUF）
3. 或暫停模型測試，專注於規則引擎與資料擷取流程的開發

---

## 三、Python 規則引擎對照（替代 LLM 測試）

雖然無法測試 LLM，但今日實作了「純規則折扣計算引擎」，作為未來 LLM 測試的基線對照組：

### 3.1 規則引擎邏輯

```python
# CartRescue 折扣審計規則引擎 v0.1

def audit_discount(list_price: int, sale_price: int, claimed_discount: str = None) -> dict:
    """
    計算實際折扣率並與標示折扣比對
    """
    if list_price <= 0 or sale_price <= 0:
        return {"error": "價格必須大於 0"}
    
    actual_rate = sale_price / list_price  # 0.65 = 6.5折
    actual_discount_折 = actual_rate * 10
    
    # 風險評級規則
    risk = "Low"
    issues = []
    
    if actual_discount_折 < 5.0:
        risk = "High"
        issues.append("實際折扣低於 5 折，可能涉及虛高原價")
    elif actual_discount_折 < 7.0:
        risk = "Medium"
        issues.append("深度折扣但未標示折扣率，消費者難以判斷")
    
    # 標示折扣一致性檢查
    if claimed_discount:
        claimed_match = re.search(r'(\d+\.?\d?)', claimed_discount)
        if claimed_match:
            claimed_rate = float(claimed_match.group(1))
            diff = abs(actual_discount_折 - claimed_rate)
            if diff > 0.5:
                risk = "High"
                issues.append(f"標示折扣({claimed_rate}折)與實際({actual_discount_折:.1f}折)差異超過 0.5 折")
    
    return {
        "list_price": list_price,
        "sale_price": sale_price,
        "actual_discount_折": round(actual_discount_折, 2),
        "risk_level": risk,
        "issues": issues,
        "savings": list_price - sale_price
    }
```

### 3.2 對今日 15 筆產品的審計結果

| # | 定價 | 會員價 | 實際折扣 | 風險 | 說明 |
|---|------|--------|---------|------|------|
| 1 | 12,800 | 8,280 | 6.5 折 | Medium | 深度折扣但未標示折扣率 |
| 2 | 15,800 | 9,080 | **5.7 折** | Medium | 深度折扣但未標示折扣率 |
| 5 | 11,800 | 7,280 | 6.2 折 | Medium | 深度折扣但未標示折扣率 |
| 6 | 13,800 | 8,080 | **5.9 折** | Medium | 深度折扣但未標示折扣率 |
| 11 | 8,800 | 6,400 | 7.3 折 | Low | 一般折扣 |

**關鍵發現**：
- **100% 的產品**（15/15）均未標示折扣率百分比
- **80% 的產品**（12/15）實際折扣低於 7 折（屬於 Medium 風險）
- **0% 的產品**標示與實際折扣不一致（因為根本沒有標示）
- 這代表 TravelPlus 的「審計風險」不在於**標示錯誤**，而在於**資訊不透明**——消費者無法一眼看出優惠幅度

---

## 四、文獻研究（新增 3 篇，累積 51 篇）

### arXiv:2607.13078 — Operational Evidence Gaps for LLMs in Fraud Detection and Risk Scoring
- **日期**：2025-07
- **與 CartRescue 相關性**：⭐⭐⭐⭐⭐
- **核心貢獻**：系統性分析 LLM 在詐欺檢測與風險評分中的「操作證據缺口」（operational evidence gaps）
- **與今日測試直接對照**：
  - 論文指出 LLM 在風險評分時常出現「過度保守」或「過度寬鬆」的偏差——與 Day 20 Kimi K3 的「無標示折扣=中高風險」問題完全吻合
  - 建議建立人類審計師與 LLM 協作的「證據鏈」（chain of evidence），而非完全依賴 LLM 判斷
  - **對 CartRescue 啟示**：我們的風險評級規則應由人類定義（如今日的 Python 規則引擎），LLM 負責執行與解釋，而非自行判斷風險等級

### arXiv:2609.27287 — SR-Fraud: An Outcome-Supervised Reflective LLM Agent Framework for Fraud Detection
- **日期**：2025-09
- **與 CartRescue 相關性**：⭐⭐⭐⭐
- **核心貢獻**：SR-Fraud 框架——透過「結果監督」讓 LLM Agent 在詐欺檢測中自我反思與修正
- **與 CartRescue 對照**：
  - SR-Fraud 的「反射機制」（reflective mechanism）可借鑑用於 CartRescue——當 LLM 發現折扣異常時，自動回溯檢查歷史價格、比對同類商品、驗證原價真實性
  - 論文提到「frozen request-time scorer」概念——CartRescue 可以將風險評分模型凍結為穩定版本，避免模型更新導致審計標準漂移

### arXiv:1902.09566 — Anomaly Detection for an E-commerce Pricing System
- **日期**：2019-02
- **與 CartRescue 相關性**：⭐⭐⭐⭐⭐
- **核心貢獻**：Walmart 電商定價系統的異常檢測方法（無監督 + 監督式）
- **與 CartRescue 對照**：
  - Walmart 使用統計方法（IQR、Z-score）檢測價格異常——CartRescue 可以結合 LLM 與傳統統計方法，互補優缺點
  - 論文提到「即時異常檢測」對大規模電商的重要性——CartRescue 的價值主張正是「即時自動審計」
  - 這篇是經典文獻，雖然是 2019 年，但仍是電商價格異常檢測的基礎參考

---

## 五、發現的問題與驚喜

### 🔴 問題

1. **API 金鑰缺失**：Cron job 執行環境中未載入任何 LLM API 金鑰，導致無法進行模型測試。這是連續 21 天測試以來**首次完全無法測試 LLM**。

2. **TravelPlus 產品頁導向問題**：點擊產品連結後被導回列表頁（而非進入產品詳情頁），可能原因：
   - 產品連結使用 `target="_blank"`，瀏覽器自動化未處理新分頁
   - 需要會員登入才能查看產品詳情
   - 網站前端路由設計問題

3. **產品名稱擷取困難**：curl 提取時，產品名稱因 HTML 結構複雜（alt 屬性 + 連結文字 + title 屬性）而難以用簡單正則精準匹配。

### 🟢 驚喜

1. **SSR 架構穩定**：curl 可直接取得完整 HTML 與價格資訊，無需 JavaScript 渲染。這表示 CartRescue 的「無瀏覽器優先」策略（curl + regex）對 TravelPlus 完全可行。

2. **純規則引擎效果良好**：僅用 Python 計算折扣率 + 簡單風險規則，就能產出有意義的審計結果。這證明 CartRescue 的**核心價值不在於 LLM 本身，而在於「結構化審計流程」**——LLM 只是增強層。

3. **文獻支持「人機協作」**：arXiv:2607.13078 證明 LLM 不應單獨做風險判斷，而應與人類規則結合——這正是 CartRescue 應採用的架構。

---

## 六、累積測試統計（Day 1–21）

| 指標 | 數值 |
|------|------|
| 累積測試天數 | 21 天 |
| 實際測試模型數 | 10 個（Day 1–20） |
| 今日測試模型數 | 0 個（API 金鑰缺失） |
| 累積文獻數 | **51 篇** |
| 提取產品數 | 21 筆（6 + 15） |
| 發現異常數 | 1 筆（Day 20：Roamers 背包無標示 5 折） |

---

## 七、明日計畫（Day 22）

1. **API 金鑰問題排查**：檢查 cron job 配置，確認 OLLAMA_API_KEY 或其他金鑰的載入方式。若無法解決，改為「純規則引擎日報」模式。

2. **多頁面產品擷取**：TravelPlus 行李箱分類有 232 筆產品（16 頁），嘗試自動化翻頁擷取全部價格。

3. **規則引擎優化**：
   - 加入「歷史價格追蹤」（同一產品不同時間的價格變化）
   - 加入「跨商品比價」（同品牌/同類型商品的折扣一致性）
   - 加入「虛高原價檢測」（定價是否遠高於市場均價）

4. **文獻研究**：持續追蹤 arXiv 上「agentic commerce + pricing anomaly」相關論文。

---

## 八、需要老闆決定的事項

1. **API 金鑰配置**：Cron job 執行時缺少 LLM API 金鑰。請確認：
   - OLLAMA_API_KEY 是否應寫入 `~/.hermes/cron/` 的環境設定？
   - 或改用其他方式（如 OpenRouter）集中管理金鑰？
   - 或暫停 LLM 測試，先專注開發純規則引擎的 MVP？

2. **測試方向調整**：
   - **方案 A**：繼續每日 LLM 測試（需解決金鑰問題）
   - **方案 B**：改為「規則引擎 + 文獻研究」模式，每週測試 1–2 個模型
   - **方案 C**：將測試目標擴展到其他電商網站（如 momo、PChome），建立多站點審計能力

---

*報告產生時間：2026-10-08 09:00 CST*  
*執行者：Scout（斯考特）| CartRescue AI*  
*累積測試天數：21 天 | 累積文獻：51 篇 | 今日 API 狀態：無可用金鑰*
