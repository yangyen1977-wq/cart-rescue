# TravelPlus 模型每日測試報告 Day 4（2026-09-21）

## 當日測試模型

| 模型 | 類型 | 狀態 |
|------|------|------|
| Gemini 3.1 Flash | 導航 | ❌ 無法測試（無 Gemini API） |
| **GLM-4.7 Flash** | 導航（本地） | ✅ 已測試，決策正確但 TTFT 過長 |

## 測試結果

### GLM-4.7 Flash（導航測試）
- **TTFT**：約 62 秒（首次）/ 122 秒（第二次）
- **成功率**：決策正確，但輸出格式異常
- **步驟數**：未執行實際瀏覽器操作，僅進行 prompt 推理測試
- **Token 消耗**：189 tokens（輸入）/ 800 tokens（輸出，被截斷）
- **成本**：免費（本地部署）
- **優點**：
  - `thinking` 欄位中完整分析出正確導航步驟：首頁→產品列表→產品頁→選擇尺寸→選擇顏色→加入購物車
  - 能理解繁體中文語境，正確識別 `#putinCart` 和 `#goShoppingCart`
- **缺點**：
  - TTFT 過長（62-122 秒），遠超可用範圍（<5秒）
  - `response` 欄位完全為空，實際內容藏在 `thinking` 欄位
  - `done_reason: length`，推理在思考過程中被截斷

## TravelPlus 網站結構分析（Day 4 更新）

### 產品頁確認（AZPAC 30吋 Trucker 3.0）
- **產品名稱**：AZPAC 30吋 Trucker 3.0 防爆煞車行李箱
- **定價**：NT:12800（特價：8280）
- **顏色選項**：象牙白、曜石黑、薄幕灰、月牙藍、松針綠（客製化按鈕 `<a>`）
- **尺寸選項**：30吋
- **放入購物車**：`#putinCart`（`<a>` 標籤）
- **立刻結帳**：`#goShoppingCart`（`<a>` 標籤）
- **索取折價券**：LINE 客服連結（`https://bit.ly/3DqMqO6`），非結帳折扣碼輸入

### 結帳流程
1. 未登入會員時，點擊「立刻結帳」會重定向到 `login.aspx`
2. 需先登入會員才能進入結帳頁面
3. 無折扣碼輸入欄位

## 發現的問題或驚喜

### 問題
1. **Ollama Cloud API 金鑰為空**：環境變數 `OLLAMA_API_KEY` 長度為 0，無法測試 kimi-k2.6 / kimi-k3 等雲端模型
2. **🚨 模型輸出欄位不一致**：GLM-4.7 Flash 將內容放在 `thinking` 欄位而非 `response` 欄位，這與 Day 1 發現的 Kimi K2.6 問題相同（`content` vs `reasoning`）
3. **本地大模型推論過慢**：19GB 的 GLM-4.7 Flash 在本地推論需 62-122 秒，不適合實時導航任務

### 驚喜
1. **GLM-4.7 Flash 決策邏輯正確**：雖然輸出格式異常，但 thinking 過程中的推理完全正確
2. **ComboShoppingBench 論文高度相關**：專門針對優惠券購物籃的基準測試

## 文獻研究進度

新增 1 篇重要論文（arXiv:2608.09282）：
- **ComboShoppingBench: Evaluating LLM Agents for Budget-Constrained Basket Shopping with Coupons**
- 專門針對「預算限制 + 優惠券」的購物籃基準測試，與 CartRescue 折扣碼審計高度相關
- 累積 10 篇

## 明日計畫

1. 繼續測試本地可用模型
2. 搜尋關於 `thinking`/`reasoning` vs `response`/`content` 輸出格式不一致問題的解決方案
3. 建立模型輸出解析的統一處理邏輯

## 附錄

### 本地可用模型清單
| 模型 | 大小 | 狀態 |
|------|------|------|
| nomic-embed-text | 274 MB | 嵌入模型 |
| glm-4.7-flash | 19 GB | 已測試（Day 4），推論過慢 |
| llama3.2:3b | 2.0 GB | 已測試（Day 2） |
| gemma3:4b | 3.3 GB | 已測試（Day 3） |
| qwen2.5:7b | 4.7 GB | 已測試（Day 3） |

### 需要老闆決定的事項
1. 是否配置 Ollama Cloud API 金鑰以測試 kimi-k2.6 / kimi-k3？
2. 是否需要建立統一的模型輸出解析邏輯（處理 `thinking`/`reasoning` 欄位）？
3. TravelPlus 無折扣碼機制，是否改用其他電商網站進行測試？
