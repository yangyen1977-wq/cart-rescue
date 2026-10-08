# TravelPlus 模型每日測試報告 Day 5（2026-09-22）

## 當日測試模型

| 模型 | 類型 | 狀態 |
|------|------|------|
| **DeepSeek V4.1 Flash** | 導航 | ✅ 已測試，內容在 reasoning 欄位 |
| **Kimi K2.6** | 導航 | ✅ 已測試，內容在 reasoning 欄位 |
| **Kimi K3** | 異常判讀 | ✅ 已測試，content 部分輸出但截斷 |

## 測試結果

### DeepSeek V4.1 Flash（導航測試）
- **TTFT**：54.7 秒
- **成功率**：決策正確（識別分類頁與產品頁連結），但輸出格式異常
- **Token 消耗**：167 tokens（輸入）/ 600 tokens（輸出，被截斷）
- **成本**：依 Ollama Cloud 計價（約 $0.0002/1K tokens）
- **優點**：
  - `reasoning` 欄位中完整分析導航步驟
  - 正確識別 `/ProductList.aspx?cid=123` 為分類頁、`/Product.aspx?id=AZ00030` 為產品頁
  - 理解「先選分類再選產品」的兩步導航邏輯
- **缺點**：
  - `content` 欄位完全為空，實際內容全在 `reasoning`
  - TTFT 過長（54.7 秒），遠超可用範圍（<5 秒）
  - `finish_reason: length`，輸出被截斷

### Kimi K2.6（導航測試）
- **TTFT**：27.4 秒
- **成功率**：決策正確，輸出格式異常（與 DeepSeek 相同問題）
- **Token 消耗**：164 tokens（輸入）/ 800 tokens（輸出，被截斷）
- **成本**：依 Ollama Cloud 計價
- **優點**：
  - `reasoning` 欄位推理過程清晰，步驟分解細緻
  - 正確區分「分類頁」與「產品詳情頁」
  - 理解繁體中文語境
- **缺點**：
  - `content` 欄位完全為空
  - TTFT 仍過長（27.4 秒）
  - `finish_reason: length`

### Kimi K3（異常判讀測試）
- **TTFT**：7.7 秒 ✅（三者中最快）
- **成功率**：content 有部分輸出（83 chars），但 reasoning 佔 2,536 tokens 後被截斷
- **Token 消耗**：298 tokens（輸入）/ 800 tokens（輸出，被截斷）
- **成本**：依 Ollama Cloud 計價
- **優點**：
  - **TTFT 顯著改善**：7.7 秒，是 Kimi K2.6 的 1/3.5、DeepSeek 的 1/7
  - `content` 欄位有實際輸出（雖然被截斷）
  - 輸出格式採用 Markdown 表格，結構化程度最高
- **缺點**：
  - `finish_reason: length`，content 僅輸出 83 字元即被截斷
  - `reasoning` 佔用大量 token（2,536 tokens），擠壓 content 輸出空間

## 🚨 重大發現：模型輸出欄位不一致問題（Day 5 確認）

### 問題描述
所有測試的推理模型（DeepSeek V4.1 Flash、Kimi K2.6、Kimi K3）均將實際回答內容放在 `reasoning` 欄位，而非標準的 `content` 欄位。

| 模型 | content 欄位 | reasoning 欄位 | 輸出狀態 |
|------|--------------|----------------|----------|
| DeepSeek V4.1 Flash | 完全空白 | 包含完整分析 | ❌ 需解析 reasoning |
| Kimi K2.6 | 完全空白 | 包含完整分析 | ❌ 需解析 reasoning |
| Kimi K3 | 部分輸出（83 字元） | 包含完整分析 | ⚠️ content 被截斷 |

### 影響
1. **CartRescue 自動化流程無法直接使用 `content` 解析**，必須改為提取 `reasoning`
2. **Token 浪費嚴重**：reasoning 過程消耗大量 token（DeepSeek 600 tokens、Kimi K2.6 800 tokens），但這些「思考過程」對最終決策並非必要
3. **TTFT 過長**：推理模型需要額外時間生成 reasoning，導致導航任務延遲 7-55 秒

### 解決方案方向
1. **建立統一解析邏輯**：優先取 `content`，若為空則取 `reasoning` 的前 N 行作為決策依據
2. **參考 SelfBudgeter 論文**（arXiv:2505.11274）：採用自適應 token 分配策略，根據任務難度動態調整 reasoning 預算
3. **使用非推理模型進行導航**：如 GLM-5.3 Flash（非 reasoning 架構），預期 TTFT < 3 秒且 content 正常輸出

## TravelPlus 網站結構分析（Day 5 更新）

透過 curl 成功抓取首頁 HTML（622,713 bytes），確認：
- **首頁標題**：t+樂遊家戶外旅遊專賣店 首頁
- **導航結構**：包含「行李箱」「背包」「配件」等分類
- **產品連結模式**：`/ProductList.aspx?cid=XXX`（分類列表）、`/Product.aspx?id=XXXXX`（產品詳情）
- **結帳限制**：未登入會員時重定向至 `login.aspx`（與 Day 1-4 一致）
- **折扣碼機制**：全站無 coupon/discount 輸入框（與 Day 1-4 一致）

## 文獻研究進度

新增 3 篇重要論文：

1. **arXiv:2505.11274 — SelfBudgeter: Adaptive Token Allocation for Efficient LLM Reasoning**
   - 專門解決 reasoning 模型 token 浪費問題
   - 提出自適應推理策略，根據查詢難度動態分配 token
   - 與 CartRescue 發現的「reasoning 佔用過多 token」問題直接相關

2. **arXiv:2607.09600 — Agora: Enhancing LLM Agent Reasoning Via Auction-Based Task Allocation**
   - 探討多專家模型協作與任務分配
   - 可用於 CartRescue「導航模型 + 異常判讀模型」的協作架構設計

3. **arXiv:2606.16650 — Understanding Automated Web GUI Testing: An LLM-Based Approach**
   - AWGT（Automated Web GUI Testing）綜述
   - 涵蓋傳統基於模型、RL、LLM 三種方法
   - 與 CartRescue 瀏覽器自動化測試方向高度相關

**累積文獻：13 篇**

## 明日計畫（Day 6）

1. **測試非推理模型**：GLM-5.3 Flash（Ollama Cloud 可用），預期無 reasoning 欄位、TTFT < 3 秒
2. **建立統一模型輸出解析函數**：處理 `content` / `reasoning` / `thinking` 欄位不一致問題
3. **嘗試實際瀏覽器自動化**：修復 browser_exec 工具（agent_helpers 模組缺失問題），或改用 playwright/curl 組合方案
4. **搜尋 momo / PChome 等電商網站的折扣碼機制**，作為 TravelPlus 的替代測試目標

## 附錄

### Ollama Cloud 可用模型清單（已確認 API 金鑰有效）
| 模型 | 類型 | 狀態 |
|------|------|------|
| deepseek-v4.1-flash | 推理（導航） | 已測試，content 空白 |
| kimi-k2.6 | 推理（導航） | 已測試，content 空白 |
| kimi-k3 | 推理（異常判讀） | 已測試，content 截斷 |
| glm-5.3 / glm-5.3-flash | 非推理（導航） | 待測試 |
| glm-5.1 / glm-5.2 | 非推理 | 待測試 |
| gemma4:31b | 非推理 | 待測試 |
| deepseek-v4-pro | 推理 | 待測試 |

### 需要老闆決定的事項
1. **TravelPlus 無折扣碼機制**，是否正式改用 momo / PChome / 蝦皮等電商進行測試？
2. **是否優先建立「非推理模型」導航管線**（如 GLM-5.3 Flash），而非繼續優化 reasoning 模型解析？
3. **是否需要申請 Gemini / OpenAI / Anthropic API 金鑰**以測試原計畫中的 GPT-4o-mini、Claude Sonnet 5、Gemini 3.1 Flash？
