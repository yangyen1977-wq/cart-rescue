# TravelPlus 模型每日測試報告 Day 9（2026-09-26）

## 當日測試模型

| 模型 | 類型 | 狀態 |
|------|------|------|
| GPT-4o | 異常判讀 | ❌ 無法測試（無 OpenAI API） |
| **Qwen2.5:7b（本地 Ollama）** | 異常判讀 | ✅ 成功 |
| **Gemma3:4b（本地 Ollama）** | 異常判讀 | ✅ 成功 |
| **GLM-4.7-Flash（本地 Ollama）** | 異常判讀 | ❌ 超時（180s timeout） |
| **Llama3.2:3b（本地 Ollama）** | 導航 | ⚠️ 動作錯誤 |
| **Qwen2.5:7b（本地 Ollama）** | 導航 | ✅ 正確 |

---

## 測試結果

### 1. 異常判讀模型測試（本地 Ollama）

由於 Ollama Cloud 仍無可用 API 金鑰，今日轉向 **本地 Ollama**（`http://localhost:11434`）進行測試。
本地可用模型：`qwen2.5:7b`、`gemma3:4b`、`glm-4.7-flash`、`llama3.2:3b`、`nomic-embed-text`。

**測試任務**：給定 TravelPlus 三層價格（定價 NT$15,800／特價 NT$9,080／會員價 NT$8,080），請模型分析是否存在異常或假折扣。

| 模型 | 反應時間 | 輸出品質 | 關鍵判斷 |
|------|---------|---------|---------|
| **Qwen2.5:7b** | ~3s | ⭐⭐⭐⭐ 結構清楚 | 認為「表面上合理」，但建議比對其他平台價格；標記為「可能的折扣不真實性」 |
| **Gemma3:4b** | ~4s | ⭐⭐⭐⭐ 詳盡 | **強烈懷疑假折扣**：指出 42.5%／48.9% 折扣「在無促銷活動下過大」；建議標記為「需謹慎評估」 |
| **GLM-4.7-Flash** | >180s | ❌ 超時無回應 | — |

#### Qwen2.5:7b 輸出摘要
> 「定價 NT$15,800 若為成本加上合理利潤，則價格結構可能合理……但建議在購買前比較不同商家價格……標記為『可能的折扣不真實性』。」

#### Gemma3:4b 輸出摘要
> 「42.5% 和 48.9% 的折扣幅度，若無明顯促銷活動，通常不會有如此大幅度……存在『假折扣』或『先漲後打折』的嫌疑……標記為『需謹慎評估』。」

**差異比較**：
- Qwen2.5 偏保守，強調「需要更多資訊才能判斷」；適合輔助審計、減少誤報。
- Gemma3 偏積極，直接指出「折扣過大」與「假折扣嫌疑」；適合需要高敏感度的異常標記場景。
- 兩者都正確計算出折扣幅度（42.5%／48.9%）與差額（NT$6,720／NT$7,720）。

---

### 2. 導航模型測試（本地 Ollama）

**測試任務**：給定 TravelPlus 產品頁元素列表，讓模型決定「加入購物車→結帳」的下一步動作。

| 模型 | 決策動作 | 正確性 | 備註 |
|------|---------|--------|------|
| **Llama3.2:3b** | `type(color_selector[0], '曜石黑')` | ❌ 錯誤 | 顏色選擇器是點擊元素而非文字輸入；動作類型錯誤 |
| **Qwen2.5:7b** | `click(#putinCart)` | ✅ 正確 | 直接選擇「放入購物車」，符合目標流程 |

**分析**：
- Llama3.2:3b 雖理解需選顏色，但誤判元素互動類型（type vs click），反映小模型對網頁元素語義理解不足。
- Qwen2.5:7b 正確略過顏色選擇（預設已有選中），直接執行加入購物車，符合「最小步驟完成任務」原則。

---

## TravelPlus 網站結構確認（Day 9 更新）

透過 browser_exec 訪問產品頁：`https://www.travelplus.com.tw/Product.aspx?ProductColorProductID=46896`

| 項目 | 狀態 |
|------|------|
| 產品頁 URL | ✅ 正常載入 |
| 產品名稱 | AZPAC 30吋 Trucker 3.0 前開行李箱 |
| 顏色選擇 | 曜石黑、薄幕灰、月牙藍、松針綠 |
| 尺寸選擇 | 30吋 |
| 數量輸入框 | `#qty` ✅ |
| 放入購物車 | `#putinCart` ✅ |
| 立刻結帳 | `#goShoppingCart` ✅ |
| 索取折價券 | `#getDiscount` ✅（仍為 LINE 詢問按鈕，非折扣碼輸入框） |
| 折扣碼輸入框 | ❌ 全站無 |

**備註**：今日嘗試透過 JavaScript 提取頁面價格文字，未成功抓取（可能為延遲渲染或 AJAX 載入）。browser_exec 截圖於頂部捲動時出現白屏，推測為網站 lazy-loading 或座標偏移問題。

---

## 發現的問題或驚喜

### ⚠️ 問題

1. **Ollama Cloud 仍無 API 金鑰**：已連續兩天（Day 8–9）無法使用雲端模型，計畫中的 GPT-4o／Gemini／Claude 全數無法測試。
2. **本地 GLM-4.7-Flash 回應極慢**：推論超過 180 秒無輸出，不適合生產環境即時審計。
3. **TravelPlus 價格提取困難**：DOM 查詢無法直接取得價格文字，需仰賴 OCR 或視覺模型解析截圖。

### 🎉 驚喜

1. **本地 Qwen2.5:7b 表現優異**：異常判讀與導航雙任務皆正確，反應時間 <5s，可視為生產級候選模型。
2. **Gemma3:4b 異常敏感度更高**：對「過大折扣」的警覺性強於 Qwen，適合與 Qwen 組成「保守+積極」雙模型審核機制。
3. **發現本地 Ollama 可穩定運行**：無需 API 金鑰即可進行模型測試，為 CartRescue 的本地部署方案提供可行性證據。

---

## 文獻研究（新增 3 篇）

累積文獻：**21 篇**

### 1. arXiv:2603.20636 — A Modular LLM Framework for Explainable Price Outlier Detection
- **日期**：2026 年 3 月
- **核心貢獻**：首次將電商價格異常標記為「基於產品語義的可解釋推理任務」
- **與 CartRescue 相關性**：⭐⭐⭐⭐⭐（最高）
- **關鍵發現**：
  - 模型不只是計算數值偏差，而是結合產品類別、品牌、規格進行語義推理
  - 輸出「解釋」——說明為何該價格被標記為異常（例如「同類型 30 吋行李箱均價 NT$12,000，此定價偏高 31%」）
- **CartRescue 應用**：可直接借鏡「可解釋異常標記」架構，讓審計報告不只給分數，還給理由

### 2. E-Commerce Bench（ecbench.github.io）
- **核心貢獻**：長期模擬電商店鋪運作的 LLM Agent benchmark（一年週期）
- **與 CartRescue 相關性**：⭐⭐⭐
- **關鍵發現**：涵蓋談判、詐騙迴避、現金流管理等任務，但偏重「經營者」視角而非「消費者保護」視角
- **CartRescue 應用**：可參考其模擬環境設計，建立 CartRescue 專屬的「結帳審計模擬器」

### 3. AD-LLM Benchmark（Bean Labs, 2026-06）
- **核心貢獻**：測試 GPT-4o 與 Llama 3.1 8B 在異常檢測三種角色（zero-shot detector、data augmenter、model selector）
- **與 CartRescue 相關性**：⭐⭐⭐⭐
- **關鍵發現**：
  - GPT-4o zero-shot AUROC 達 0.93–0.99
  - **但 LLM-based model selection 仍不可靠**
  - 對金融審計 AI 有直接啟示：「偵測準」≠「選模型準」，需分開評估
- **CartRescue 應用**：若未來採多模型路由（如 Qwen 保守判斷 + Gemma 積極判斷），需建立獨立的「模型選擇器」評估機制

---

## 模型測試進度總覽（Day 1–9）

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
| 9 | 09/26 | GPT-4o | Qwen2.5:7b、Gemma3:4b、Llama3.2:3b（本地） | Qwen ✅、Gemma ✅、Llama ❌ |

**本地模型測試初探（Day 9 新增）**：
- ✅ 本地可用且表現良好：Qwen2.5:7b（導航+異常皆通）、Gemma3:4b（異常敏感度最高）
- ❌ 本地不可用／不穩定：GLM-4.7-Flash（超時）
- ⚠️ 本地小模型有限制：Llama3.2:3b（元素互動類型理解錯誤）

---

## 明日計畫（Day 10）

1. **繼續本地模型測試**：測試 `llama3.2:3b` 在更詳細 prompt（含元素類型說明）下的導航表現
2. **若取得 API 金鑰**：優先補測 GPT-4o（原定 Day 9 目標）與 Kimi K3（原定 Day 10 目標）
3. **browser_exec 強化**：嘗試用視覺分析（vision_analyze）解析產品頁截圖中的價格資訊，解決 DOM 提取失效問題
4. **文獻研究**：深入閱讀 arXiv:2603.20636，提取「可解釋價格異常檢測」的具體方法論

---

## 需要老闆決定的事項

1. **API 金鑰配置**：Ollama Cloud／OpenAI／Gemini／Anthropic 已連續兩天無法使用。是否需要配置任一雲端 API key，或改以「本地 Ollama + 開源模型」為主要架構？
2. **本地部署可行性**：Day 9 證明本地 Qwen2.5:7b 可勝任導航+異常雙任務，且無需外部 API 成本。是否將「本地開源模型」納入 CartRescue MVP 技術方案？
3. **測試目標調整確認**：TravelPlus 無折扣碼機制，三層價格（定價／特價／會員價）審計已成為實際測試場景。是否正式將產品定位從「折扣碼審計」擴展為「電商價格異常與 dark pattern 審計」？
