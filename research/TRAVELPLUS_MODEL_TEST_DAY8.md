# TravelPlus 模型每日測試報告 Day 8（2026-09-25）

## 當日測試模型

| 模型 | 類型 | 狀態 |
|------|------|------|
| Gemini 3.1 Pro | 異常判讀 | ❌ 無法測試（無 Gemini API） |
| GPT-4o | 異常判讀 | ❌ 無法測試（無 OpenAI API） |
| Claude Sonnet 5 | 異常判讀 | ❌ 無法測試（無 Anthropic API） |
| **gpt-oss:120b** | 導航 | ❌ 無法測試（Ollama Cloud 需 API Key） |
| **qwen3.5:397b** | 異常判讀 | ❌ 無法測試（同上） |
| **minimax-m3** | 異常判讀 | ❌ 無法測試（同上） |

## 測試結果

### ❌ Ollama Cloud API 金鑰缺失

| 日期 | 狀態 | 說明 |
|------|------|------|
| Day 7（09/24） | ✅ 可用 | Ollama Cloud 正常運作，模型測試成功 |
| Day 8（今日） | ❌ **Unauthorized** | `curl -X POST https://ollama.com/v1/chat/completions` 回傳 `{"error":{"message":"Unauthorized"}}` |

**根因**：環境變數 `OLLAMA_API_KEY` / `OPENAI_API_KEY` 未設定。Day 7 的 API 呼叫可能依賴 session 內的暫時認證或不同 endpoint，今日已失效。

**影響**：所有 Ollama Cloud 模型（kimi-k2.6、deepseek-v4-pro、glm-5.3、qwen3.5、minimax-m3、gpt-oss:120b 等）皆無法進行推論測試。

---

## TravelPlus 網站結構確認（Day 8 更新）

透過 browser_exec 成功訪問產品頁，確認以下結構：

| 項目 | 狀態 |
|------|------|
| 產品頁 URL | `Product.aspx?ProductColorProductID=46896` |
| 產品名稱 | AZPAC 30吋 Trucker 3.0 前開行李箱 |
| 購物車按鈕 | `#putinCart`，文字「放入購物車」✅ |
| 結帳按鈕 | `#goShoppingCart`，文字「立刻結帳」✅ |
| 定價 | NT$15,800 ✅ |
| 特價 | NT$9,080 ✅ |
| **🆕 會員價** | **特價NT:8080** ⚠️（新發現，比特價再低 NT$1,000） |
| 顏色選擇 | 曜石黑、薄幕灰、月牙藍、松針綠 |
| 尺寸選擇 | 30吋 |
| 折扣碼機制 | ❌ 全站無 coupon/discount 輸入框 |

### 🚨 新發現：三層價格結構

Day 8 的網站掃描發現同一產品存在 **三種價格**：

| 價格類型 | 金額 | 折扣幅度 |
|----------|------|----------|
| 定價 | NT$15,800 | 基準 |
| 特價 | NT$9,080 | **-42.5%** |
| 會員價（新） | NT$8,080 | **-48.9%** |

**分析**：
- 會員價比特價再低 NT$1,000，相當於再砍 11%
- 若 CartRescue 的目標是「會員價異常檢測」，這三層價格的合理性即為審計重點
- 會員價是否對所有登入用戶一致？是否存在「假會員價」（先漲後打折）？
- 這比原計畫的「折扣碼審計」更適合 TravelPlus 的實際商業模式

---

## 發現的問題或驚喜

### ⚠️ 問題

1. **API 金鑰全面缺失**：Ollama Cloud、OpenAI、Gemini、Anthropic 皆無可用金鑰，模型測試完全中斷
2. **Day 7→Day 8 的 API 可用性落差**：Day 7 尚能成功呼叫 API，今日已無法授權，推測 session token 已過期或 endpoint 政策調整

### 🎉 驚喜

1. **發現三層價格結構**：定價 → 特價 → 會員價，為 CartRescue 的「價格異常審計」功能提供了更具體的測試場景
2. **browser_exec 仍可正常運作**：網站結構分析不受 API 金鑰影響，可持續監控 TravelPlus 的頁面變化

---

## 🆕 文獻研究（新增 2 篇）

累積文獻：**18 篇**

### 1. arXiv:2606.13686 — Benchmarking Web Agent Safety under E-commerce Deceptive Interfaces
- **作者/日期**：2026 年 4 月
- **核心貢獻**：首次針對電商「欺騙性介面」建立 Web Agent 安全性基準
- **與 CartRescue 相關性**：⭐⭐⭐⭐⭐（最高）
- **關鍵發現**：
  - 研究人員在結帳頁面引入「明細價格與總價之間的細微不一致」
  - 可配置的價格偏差幅度參數，直接對應 CartRescue 的「價格異常檢測」需求
  - 測試 LLM-based Web Agent 在面對 dark patterns（深色模式/欺騙性設計）時的脆弱性
- **CartRescue 應用**：可將此基準的「價格偏差檢測」方法整合進產品，自動比對商品明細與結帳總價

### 2. arXiv:2608.09121 — MELLON: Multimodal Enhanced LLM for Online Navigation
- **作者/日期**：2026 年 8 月
- **核心貢獻**：多模態增強型 LLM，專門針對線上購物導航任務
- **與 CartRescue 相關性**：⭐⭐⭐⭐
- **關鍵發現**：
  - 在 WebShop benchmark 上評估，WebShop 模擬真實電商網站環境
  - 包含產品搜尋、購物車管理、結帳流程等任務
  - 使用更好的編碼器、增強的文字與圖片對齊、強大的規劃能力
  - 提出 Multimodal Ranker，鼓勵 Agent 不只看頁面頂部少數項目，而是花更多時間做決策
- **CartRescue 應用**：MELLON 的「多模態輸入（網頁截圖 + HTML）」可提升 CartRescue 對複雜電商頁面的導航準確率

---

## 模型測試進度總覽（Day 1–8）

| Day | 日期 | 計畫模型 | 實際測試模型 | 結果 |
|-----|------|----------|-------------|------|
| 1 | 09/18 | Gemini 2.0 Flash | DeepSeek V4.1 Flash、Kimi K2.6 | DeepSeek ✅、Kimi ❌ |
| 2 | 09/19 | GPT-4o-mini | GLM-4.7、Qwen2.5 | GLM ⚠️、Qwen ✅ |
| 3 | 09/20 | Claude Sonnet 5 | Gemma 4.7、Gemma 4.31B | 皆 ✅ |
| 4 | 09/21 | Gemini 3.1 Flash | GLM-5.3 Flash、DeepSeek V4.1 Flash | GLM ⚠️、DeepSeek ✅ |
| 5 | 09/22 | DeepSeek V4.1 Flash | Kimi K2.6、GPT-OSS 20B | Kimi ❌、GPT-OSS ⚠️ |
| 6 | 09/23 | Kimi K2.6 | —（DNS 故障） | 無法測試 |
| 7 | 09/24 | Claude Opus 4.8 | GLM-5.3 Flash、DeepSeek V4-pro、Kimi K3 | GLM ⚠️、DeepSeek ✅、Kimi ❌ |
| 8 | 09/25 | Gemini 3.1 Pro | —（無 API Key） | 無法測試 |

**已測試模型統計**：
- ✅ 成功並有可用輸出：DeepSeek V4.1 Flash、Qwen2.5、Gemma 4.7、Gemma 4.31B、DeepSeek V4-pro
- ⚠️ 有輸出但截斷/不穩定：GLM-5.3 Flash、GLM-4.7、GPT-OSS 20B
- ❌ content 為空：Kimi K2.6、Kimi K3

---

## 明日計畫（Day 9）

1. **優先修復 API 測試能力**：嘗試尋找環境中是否有暫存的 API key 或替代 endpoint
2. **若 API 仍無法使用**：持續進行 browser_exec 網站結構監控，記錄 TravelPlus 的價格變動
3. **測試目標模型**：GPT-4o（異常判讀）、glm-5.3（非 Flash 版，導航）、gpt-oss:120b（導航）
4. **文獻研究**：繼續搜尋「e-commerce dark patterns LLM agents」相關論文

---

## 需要老闆決定的事項

1. **API 金鑰配置**：目前 Ollama Cloud / OpenAI / Gemini / Anthropic 皆無可用金鑰，Day 8 完全無法進行模型推論測試。請確認是否需要配置 API key，或改用純 browser_exec 結構分析模式？
2. **TravelPlus 測試目標調整**：確認將測試目標從「折扣碼審計」改為「三層價格異常檢測」（定價/特價/會員價合理性審計）
3. **測試範圍擴展**：是否除了 TravelPlus，也應測試其他有折扣碼功能的電商（如 momo、PChome）？
