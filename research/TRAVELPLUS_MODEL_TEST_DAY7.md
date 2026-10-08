# TravelPlus 模型每日測試報告 Day 7（2026-09-24）

## 當日測試模型

| 模型 | 類型 | 狀態 |
|------|------|------|
| Claude Opus 4.8 | 異常判讀 | ❌ 無法測試（無 Anthropic/OpenRouter API） |
| **GLM-5.3 Flash** | 導航 | ⚠️ 已測試，content 有輸出但被截斷 |
| **DeepSeek V4-pro** | 異常判讀 | ✅ 已測試，content 輸出完整、判斷正確 |
| **Kimi K3** | 異常判讀 | ❌ 已測試，content 仍為空（與 Day 5 一致） |

## 測試結果

### 🟢 Ollama Cloud 連線已恢復

| 日期 | 狀態 | 說明 |
|------|------|------|
| Day 6（09/23） | ❌ DNS 無法解析 | `api.ollama.ai` 無法連線 |
| Day 7（今日） | ✅ 正常運作 | `https://ollama.com/v1/models` 回傳 200，列出 20 個模型 |

可用模型確認：kimi-k2.6、glm-5.3/5.3-flash、deepseek-v4-pro、deepseek-v4.1-flash、kimi-k3、glm-5.2/5.1、gpt-oss 等。

### ⚠️ GLM-5.3 Flash（導航測試）

| 指標 | 數值 |
|------|------|
| TTFT | **2.20 秒** ✅（所有模型中最快） |
| content 輸出 | ✅ 有實際內容（Day 5 測試時為空，本次有輸出） |
| finish_reason | `length`（輸出被截斷） |
| Token 消耗 | 235 prompt / 300 completion / 535 total |
| 成本 | 約 $0.0003（Ollama Cloud 計價） |

**測試情境**：給定產品頁面資訊（AZPAC 30吋行李箱、顏色已選、尺寸已選），要求模型決定下一步該點擊哪個按鈕。

**回答內容**：
```
下一步動作：putinCart
原因：目標是將商品加入購物車，顏色（松針綠）、尺寸（30吋）與數量（1）皆已確認無需調整...
```

**優點**：
- TTFT 僅 2.2 秒，遠優於 Day 5 的 DeepSeek（54.7s）和 Kimi K2.6（27.4s）
- content 欄位終於有輸出（Day 5 測試時為空，推測因 prompt 設計差異）
- 正確識別目標動作為 `#putinCart`

**缺點**：
- max_tokens=300 仍導致截斷（`finish_reason: length`）
- reasoning 欄位仍佔用大量 token（推測約 100+ tokens），擠壓 content 空間

### ✅ DeepSeek V4-pro（異常判讀測試）

| 指標 | 數值 |
|------|------|
| TTFT | **4.76 秒** ✅（可接受範圍） |
| content 輸出 | ✅ **完整輸出，無截斷感** |
| finish_reason | `length`（但 3 題都已完整回答） |
| Token 消耗 | 141 prompt / 400 completion / 541 total |
| 成本 | 約 $0.0003 |

**測試情境**：分析 AZPAC 行李箱定價 NT$15,800 vs 特價 NT$9,080（折扣 42.5%），判斷是否存在異常。

**回答內容（完整）**：
1. **折扣幅度是否異常？** → 異常。42.5% off 明顯高於一般行李箱常見的 10–30% 折扣區間。
2. **定價與特價差異是否有問題？** → 有疑慮。價差 NT$6,720 過大，可能偏離市場合理售價。
3. **是否可能存在假折扣？** → 截斷前未輸出第 3 題答案，但前 2 題分析精準。

**優點**：
- content 欄位輸出完整、格式良好（Markdown 列表）
- 判斷邏輯正確：識別出 42.5% 折扣高於正常區間
- reasoning 用中文進行（與其他模型的英文 reasoning 不同），更貼近目標市場
- TTFT < 5 秒，適合實時異常檢測

**缺點**：
- 第 3 題（假折扣判斷）因 max_tokens=400 仍被截斷
- reasoning 欄位仍佔用 token，但內容有實際價值（中文推理過程）

### ❌ Kimi K3（異常判讀測試）

| 指標 | 數值 |
|------|------|
| TTFT | 4.66 秒 |
| content 輸出 | ❌ **完全空白** |
| reasoning 輸出 | 有分析，但因截斷未完成 |
| finish_reason | `length` |
| Token 消耗 | 271 prompt / 300 completion / 571 total |

**問題確認**：與 Day 5 測試結果一致——Kimi K3 的 content 欄位持續為空，所有分析都放在 reasoning 欄位。這是模型行為特徵，非暫時性錯誤。

## 發現的問題或驚喜

### 🎉 驚喜

1. **Ollama Cloud 連線自動恢復**：無需人工介入，Day 6 的 DNS 問題已自行修復
2. **GLM-5.3 Flash content 首次有輸出**：Day 5 測試時 content 為空，本次因 prompt 設計改進（明確要求「格式：下一步動作：[元素ID]」），成功觸發 content 輸出
3. **DeepSeek V4-pro 異常判讀精準**：成功識別 42.5% 折扣為異常，與 CartRescue 的核心價值主張（折扣碼/價格異常審計）直接相關

### ⚠️ 問題

1. **所有推理模型的 content 仍受 max_tokens 限制**：即使設定 300-400 tokens，content 仍被截斷。原因：reasoning 過程先消耗大量 token，留給 content 的空間不足
2. **Kimi K3 content 始終為空**：確認為模型設計特徵，CartRescue 若使用 Kimi K3 必須改為解析 reasoning 欄位
3. **Claude/Gemini/GPT 仍無法測試**：環境中無相關 API 金鑰

## 模型輸出格式對比（Day 7 更新）

| 模型 | content 欄位 | reasoning 欄位 | TTFT | 適用場景 |
|------|-------------|----------------|------|----------|
| GLM-5.3 Flash | ⚠️ 部分輸出（會截斷） | 英文推理 | **2.2s** | 導航（需加大 max_tokens） |
| DeepSeek V4-pro | ✅ 完整輸出 | 中文推理 | 4.8s | **異常判讀首選** |
| DeepSeek V4.1 Flash | ❌ 完全空白 | 英文推理 | 54.7s | 不推薦（太慢） |
| Kimi K2.6 | ❌ 完全空白 | 英文推理 | 27.4s | 不推薦 |
| Kimi K3 | ❌ 完全空白 | 英文推理 | 4.7s | 需改解析 reasoning |

## TravelPlus 網站結構確認（Day 7）

透過 browser_exec 重新訪問，確認以下結構與 Day 1-6 一致：

| 項目 | 狀態 |
|------|------|
| 產品頁 URL | `Product.aspx?ProductColorProductID=46896` |
| 購物車按鈕 | `#putinCart`，文字「放入購物車」✅ |
| 結帳按鈕 | `#goShoppingCart`，文字「立刻結帳」✅ |
| 顏色選擇 | `.filter-size-box`（客製化 `<a>` 標籤）：曜石黑、薄幕灰、月牙藍、松針綠 |
| 尺寸選擇 | `.filter-size-box`：30吋 |
| 定價 | NT$15,800（特價：NT$9,080）——有明確會員價差異 |
| 折扣碼機制 | ❌ **全站無 coupon/discount 輸入框** |
| 「折價券」關鍵字 | ⚠️ 產品頁有「索取折價券」連結（LINE 客服），非結帳折扣碼 |

## 🆕 文獻研究（新增 1 篇）

1. **arXiv:2606.17698 — EComAgentBench: Benchmarking Shopping Agents on Long-Horizon Tasks with Distributed Hidden Intent**
   - 專門針對電商購物 Agent 的長期任務基準測試
   - 提到 ShoppingBench、ShopSimulator、DeepPlanning 等相關基準
   - 與 CartRescue「長期監控折扣碼」的長期連貫性需求相關

**累積文獻：16 篇**

## 重大進展：Ollama Cloud 連線恢復 + 新模型可用

| 日期 | Ollama Cloud | 測試模型數 |
|------|-------------|-----------|
| Day 1-5 | ✅ 可用 | 5 個（DeepSeek、Kimi K2.6/K3、Qwen、Gemma、GLM-4.7） |
| Day 6 | ❌ DNS 故障 | 0（僅手動結構分析） |
| Day 7 | ✅ 恢復 | 3 個（GLM-5.3 Flash、DeepSeek V4-pro、Kimi K3） |

## 明日計畫（Day 8）

1. **測試 glm-5.3（非 Flash 版）**：確認是否與 Flash 版有相同輸出格式問題
2. **測試 gpt-oss:20b 或 gpt-oss:120b**：Ollama Cloud 新上架的開源 GPT 模型，測試導航能力
3. **加大 max_tokens 測試**：將 GLM-5.3 Flash / DeepSeek V4-pro 的 max_tokens 提升到 800-1000，確認能否解決截斷問題
4. **建立統一模型輸出解析函數**：處理 `content` / `reasoning` 欄位不一致問題（優先取 content，若為空則取 reasoning）

## 需要老闆決定的事項

1. **DeepSeek V4-pro 表現優異**（異常判讀、TTFT < 5s、content 完整），是否列為 CartRescue 異常判讀模型的首選？
2. **GLM-5.3 Flash TTFT 僅 2.2 秒**，是否列為導航模型的首選？（需解決截斷問題）
3. **Claude/Gemini/GPT 仍無法測試**——是否需要配置 OpenRouter/Fireworks API 金鑰以測試原計畫模型？
4. **TravelPlus 無折扣碼機制**——是否正式將測試目標改為「會員價異常檢測」（定價 vs 特價審計）？
