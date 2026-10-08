# TravelPlus 模型每日測試報告 Day 6（2026-09-23）

## 當日測試模型

| 模型 | 類型 | 狀態 |
|------|------|------|
| **GLM-5.3 Flash** | 導航 | ❌ 無法測試（Ollama Cloud 無法連線） |
| GPT-4o-mini | 導航 | ❌ 無法測試（無 API 金鑰） |
| Claude Sonnet 5 | 異常判讀 | ❌ 無法測試（無 API 金鑰） |
| **瀏覽器結構分析** | 網站審計 | ✅ 手動完成 |

## 測試結果

### 🔴 Ollama Cloud 連線異常

```
curl: (6) Could not resolve host: api.ollama.ai
```

- 環境變數中無 `OLLAMA_API_KEY`
- 主機無法解析 `api.ollama.ai`（DNS 問題或網路限制）
- 前幾日的 Day 1-5 報告顯示 API 曾有效，今日環境可能有變

### 🟢 TravelPlus 產品頁結構分析（browser_exec 成功）

| 項目 | 發現 |
|------|------|
| **產品頁 URL** | `Product.aspx?ProductColorProductID=46896` |
| **購物車按鈕** | `#putinCart`，文字「放入購物車」✅ |
| **結帳按鈕** | `#goShoppingCart`（首頁右上角「前往結帳」） |
| **數量輸入框** | `#buyQty`（`product-amount-input`） |
| **顏色選擇** | 客製化按鈕（曜石黑、薄暮灰、月牙藍、松針綠），非標準 `<select>` |
| **尺寸選擇** | 同樣為客製化按鈕 |
| **定價顯示** | 定價 NT$15800（特價：NT$9080）——有明確會員價差異 |
| **折扣碼機制** | ❌ 全站無 coupon/discount 輸入框 |
| **會員價機制** | ⚠️ 產品頁顯示「定價 vs 特價」，可能為會員折扣 |

#### 關鍵發現：產品頁有「折價」關鍵字
產品頁 `innerText` 包含「折價」字樣，但這是指「會員價/特價」的標示，非結帳折扣碼輸入框。

## 🆕 文獻研究（新增 2 篇）

1. **arXiv:2608.30730 — E-Commerce Bench: Evaluating LLM Agents on Long-Horizon Autonomous Business Operation**
   - 長期連貫性基準，與 CartRescue 持續監控折扣碼的長期任務相關
   - 提到 Vending-Bench 2（2026）擴展到一年對抗供應商

2. **arXiv:2607.28956 — MerchantBench: Benchmarking LLM Agents for Long-Term Coherence in E-Commerce Operations**
   - 商家端 LLM Agent 長期一致性基準
   - 涵蓋購物、店面互動、客戶支援、商家工作流

**累積文獻：15 篇**

## 重大問題：Ollama Cloud 連線中斷

| 日期 | Ollama Cloud 狀態 |
|------|-------------------|
| Day 1-5 | ✅ 可用（已測試 DeepSeek、Kimi K2.6/K3） |
| Day 6（今日） | ❌ DNS 無法解析 `api.ollama.ai` |

可能原因：
1. DNS 設定變更
2. 網路環境限制（防火牆、代理）
3. Ollama Cloud 服務端變動（域名或 API 端點更改）

## 明日計畫（Day 7）

1. **修復 Ollama Cloud 連線**：
   - 嘗試 `api.ollama.com` 或其他備用端點
   - 檢查本地 Ollama 是否可用（`ollama list`）

2. **若 Ollama 仍無法使用**：
   - 轉向測試本地模型（LLaMA、Qwen、GLM 本地版）
   - 或改用替代方案：透過 browser_exec 的 `cdp()` 與網頁互動，不依賴 LLM API

3. **文獻持續追蹤**：搜尋「web agent benchmark 2026」相關新論文

## 需要老闆決定的事項

1. **Ollama Cloud 連線中斷**——是否需要我嘗試其他 API 端點，或等待環境修復？
2. **API 金鑰配置**——前幾日報告提到 `.env` 中有 `OLLAMA_API_KEY`，今日環境變數中已無此值。是否需要重新配置？
3. **TravelPlus 測試策略**——無折扣碼機制，是否正式將測試目標改為「會員價異常檢測」（定價 vs 特價差異審計）？
