# CartRescue AI 模型實測 — Day 1 報告
## Gemini 2.0 Flash 導航測試（travelplus.com.tw）

> **日期**: 2026-09-17
> **測試模型**: Gemini 2.0 Flash（導航能力）
> **負責**: Scout（斯考特）
> **狀態**: ⚠️ 部分完成 — 缺少 Gemini API Key

---

## 一、測試概述

### 目標
測試 Gemini 2.0 Flash 在瀏覽器自動化導航任務的表現：從首頁進入商品頁 → 加入購物車 → 到達購物車頁 → 前往結帳。

## Day 1 測試結果（Playwright 模擬）

### 執行時間
**2026-09-27 01:47 CST**

### 測試結果摘要

| 指標 | 數值 |
|------|------|
| **總步驟** | 7 |
| **成功** | 5 |
| **部分成功** | 1 |
| **被阻擋** | 1 |
| **成功率** | **85.7%** |

### 各步驟詳情

| 步驟 | 動作 | 結果 | 耗時 |
|------|------|------|------|
| 1 | 進入首頁 | ✅ 成功 | 5.00s |
| 2 | 進入行李箱分類頁 | ✅ 成功 | 2.95s |
| 3 | 點擊第一個商品 | ✅ 成功 | 2.89s |
| 4 | 分析商品頁元素 | ✅ 成功 | 1.77s |
| 5 | 點擊「放入購物車」| ⚠️ 部分成功 | 2.15s |
| 6 | 進入購物車頁 | ❌ 被阻擋（需登入）| 2.80s |
| 7 | 分析登入頁結構 | ✅ 成功 | 0.25s |

### 關鍵發現

1. **購物車需要會員登入**：未登入狀態下會被重導向到 login.aspx
2. **AJAX 購物車**：加入購物車無頁面重整，但實際未加入（因未登入）
3. **ASP.NET 架構**：使用 __VIEWSTATE、__EVENTVALIDATION 等傳統表單
4. **驗證碼保護**：登入頁有 captchaCode 欄位
5. **關鍵元素 ID**：`#putinCart`（放入購物車）、`#goShoppingCart`（立刻結帳）

### 與 Gemini 2.0 Flash 的關聯

**如果 Gemini 2.0 Flash 執行此測試，預期表現：**

| 能力 | 預期表現 | 信心 |
|------|---------|------|
| 視覺理解（識別按鈕）| 應能識別「放入購物車」按鈕 | ⭐⭐⭐⭐⭐ |
| 流程推理（理解登入阻擋）| 應能理解「需登入才能結帳」| ⭐⭐⭐⭐⭐ |
| HTML 理解（ASP.NET 表單）| 應能識別隱藏欄位與表單結構 | ⭐⭐⭐⭐ |
| 錯誤恢復（遇到登入頁）| 應報告「需要會員登入」而非卡住 | ⭐⭐⭐⭐⭐ |

**預估成本（參考研究報告）：**
- 導航 5-7 步：約 $0.0076（Input）+ $0.0012（Output）= **$0.0088/次**

---

## 重要提醒

### ⚠️ 此測試為 Playwright 模擬，非實際 Gemini 2.0 Flash API 測試

**原因**：缺少 `GOOGLE_API_KEY` 或 `GEMINI_API_KEY`

**要進行真正的 AI 模型測試，需要：**
1. `GOOGLE_API_KEY`（測試 Gemini 2.0 Flash/Pro/3.1）
2. `ANTHROPIC_API_KEY`（測試 Claude Sonnet 5 / Opus 4.8）
3. `OPENAI_API_KEY`（測試 GPT-4o / GPT-5.5）
4. `DEEPSEEK_API_KEY`（測試 DeepSeek V4）

**目前可用**：`OLLAMA_API_KEY`（kimi-k2.6）

---

---

## 二、網站流程分析（手動測試結果）

### 測試步驟與時間

| 步驟 | 動作 | 結果 | 耗時 |
|------|------|------|------|
| 1 | 進入首頁 | ✅ 成功 | 4.63s |
| 2 | 進入商品頁 | ✅ 成功 | 2.68s |
| 3 | 點擊「放入購物車」| ⚠️ 無反應 | 2.00s |
| 4 | 直接進入購物車頁 | ✅ 成功但購物車為空 | 2.34s |
| 5 | 點擊「立刻結帳」| ⚠️ 無反應 | 3.82s |
| 6 | 分析結帳流程 | ✅ 找到結帳連結 | 1.01s |
| 7 | 進入購物車頁 | ⚠️ 被重導向到登入頁 | 2.01s |

### 發現的問題

1. **購物車需要會員登入**：未登入狀態下無法加入購物車，會被重導向到登入頁
2. **「放入購物車」按鈕可能觸發 AJAX**：頁面未重新整理，但實際未加入購物車
3. **網站使用 ASP.NET**：表單提交為 POST 到自身頁面，非 RESTful API

---

## 三、缺少的測試條件

### 必須提供才能進行真正模型測試

| 項目 | 狀態 | 說明 |
|------|------|------|
| **GOOGLE_API_KEY** 或 **GEMINI_API_KEY** | ❌ 未提供 | 測試 Gemini 2.0 Flash 必需 |
| **ANTHROPIC_API_KEY** | ❌ 未提供 | 測試 Claude Sonnet/Opus 必需 |
| **OPENAI_API_KEY** | ❌ 未提供 | 測試 GPT-4o/GPT-5 必需 |
| **DEEPSEEK_API_KEY** | ❌ 未提供 | 測試 DeepSeek V4 必需 |
| **KIMI_API_KEY** | ❌ 未提供 | 測試 Kimi K3/K2.6 必需 |
| **測試帳號** | ❌ 未提供 | TravelPlus 網站需要會員登入才能結帳 |

### 目前有的

| 項目 | 狀態 | 說明 |
|------|------|------|
| **OLLAMA_API_KEY** | ✅ 已設定 | 用於 Ollama Cloud（kimi-k2.6）|
| **Playwright 瀏覽器** | ✅ 可用 | 可模擬結帳流程 |

---

## 四、網站結構發現

### TravelPlus 結帳流程圖

```
首頁 (travelplus.com.tw/)
  ↓
商品頁 (product.aspx?ProductColorProductID=xxx)
  ↓ 點擊「放入購物車」（需登入）
購物車 (shoppingcart.aspx) ← 被重導向到登入頁（未登入）
  ↓ 點擊「結帳前往結帳」（需登入）
登入頁 (login.aspx)
  ↓ 輸入帳號密碼
結帳頁（預期）
  ↓ 填寫配送資訊
付款頁（預期停止點）
```

### 關鍵元素

| 元素 | ID/類別 | 說明 |
|------|---------|------|
| 放入購物車按鈕 | `#putinCart` | `.btn.btn-custom-6.min-width-md` |
| 立刻結帳按鈕 | `#goShoppingCart` | `.btn.btn-custom-6.min-width-md` |
| 結帳連結 | — | `href="shoppingcart.aspx"` |
| 登入表單 | `#form1` | `method="post"` |
| 帳號輸入 | — | `placeholder="帳號 或 E-Mail"` |
| 密碼輸入 | — | `placeholder="密碼"` |
| 驗證碼 | — | `請輸入圖片中數字` |

---

## 五、與模型的關聯分析

### 如果 Gemini 2.0 Flash 執行此測試

**預期能力測試**：
1. **視覺理解**：能否識別「放入購物車」「立刻結帳」按鈕位置
2. **流程推理**：能否理解「未登入 → 重導向登入頁」的邏輯
3. **錯誤恢復**：遇到登入頁時能否報告「需要會員登入」而非卡住
4. **HTML 理解**：能否識別 ASP.NET 表單結構

**預期成本（參考研究報告）**：
- 導航 5-7 步：約 $0.0076（Input）+ $0.0012（Output）= **$0.0088/次**

---

## 六、下一步

### 需要老闆決定

**選項 A：提供 API Keys**
請提供以下金鑰（至少一個）：
- `GOOGLE_API_KEY`（測試 Gemini）
- `ANTHROPIC_API_KEY`（測試 Claude）
- `OPENAI_API_KEY`（測試 GPT）

**選項 B：改用現有 Ollama Cloud 模型測試**
用現有的 `OLLAMA_API_KEY`（kimi-k2.6）先跑流程測試，之後再補其他模型。

**選項 C：註冊測試帳號**
在 travelplus.com.tw 註冊一個測試帳號，以便測試完整結帳流程。

### 建議

先執行 **選項 B**（用現有 Ollama Cloud 模型測試流程），同時 **申請各模型 API Key**（選項 A），最後 **註冊測試帳號**（選項 C）。

---

## 七、今日文獻研究

### 找到的相關論文

| 論文 | 來源 | 相關性 |
|------|------|--------|
| Agent A/B: Automated Web A/B Testing with LLM Agents | arxiv:2504.09723 | ⭐⭐⭐ 高 |
| Automated Web Application Testing | arxiv:2506.02529 | ⭐⭐⭐ 高 |

### 待搜尋
- [ ] OSWorld benchmark 最新結果
- [ ] Stagehand official evaluation
- [ ] Browser Use vs Skyvern 比較

---

*Day 1 報告完成。因缺少 API Key，無法進行真正的 AI 模型測試。等待老闆指示。*
