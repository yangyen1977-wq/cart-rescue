# CartRescue AI 模型實測 — Day 2 報告

> **日期**: 2026-09-19
> **測試目標網站**: https://www.travelplus.com.tw/
> **負責**: Scout（斯考特）
> **狀態**: Day 2 完成 — API 限制持續，改採本地模型測試

---

## 一、當日測試模型

### 原定測試：GPT-4o-mini（導航模型）

**狀態**: ❌ 無法測試
**原因**: 環境無 OpenAI API 金鑰。config.yaml 設定為 `provider: ollama-cloud`，base_url 指向 Ollama Cloud。Ollama Cloud 模型清單中無 GPT-4o-mini。

### 實際測試（本地 Ollama 模型）

| 模型 | 類型 | 狀態 | 說明 |
|------|------|------|------|
| **LLaMA 3.2 3B** | 導航（本地） | ✅ 已測試 | 理解導航任務，但決策準確度有限 |
| **GLM-4.7 Flash** | 導航（本地） | ⚠️ Timeout | 19GB 模型，120 秒未回應 |

---

## 二、API 環境更新

### 發現：OLLAMA_API_KEY 已配置

`.env` 檔案中 `OLLAMA_API_KEY=***` 已設置，表示金鑰存在但可能被加密/遮罩。

### 環境配置對照

| 來源 | Provider | Base URL |
|------|----------|----------|
| config.yaml | `ollama-cloud` | `https://ollama.com/v1` |
| .env | `OLLAMA_API_KEY` 已設 | 未覆寫 |

### 本地 Ollama 服務狀態

- 本地 Ollama 服務運行中（PID 3610，自 8月15日啟動）
- 可用本地模型：
  - `nomic-embed-text:latest` (137M)
  - `glm-4.7-flash:latest` (29.9B, Q4_K_M)
  - `llama3.2:3b` (3.2B)
  - `gemma3:4b` (4B)
  - `qwen2.5:7b` (7B)

**問題**：本地模型列表中無 DeepSeek、Kimi、GPT-OSS 等目標模型。Ollama Cloud 模型需透過 API 呼叫，無法直接列舉。

---

## 三、網站結構深入分析（產品頁級別）

### 測試產品頁

**URL**: `https://www.travelplus.com.tw/Product.aspx?ProductColorProductID=46797&cid=436`
**產品**: AZPAC 30吋 Trucker 3.0 防爆煞車行李箱

### 產品頁結構

```
產品頁
  ├── 產品名稱: AZPAC 30吋 Trucker 3.0 防爆煞車行李箱
  ├── 款 式: Az00330
  ├── 品 牌: AZPAC
  ├── 定價 NT: 12800
  ├── 特價 NT: 8280（約 6.5 折）
  ├── 顏色選擇（非標準 <select>）
  │     ├── 象牙白
  │     ├── 曜石黑
  │     ├── 薄幕灰
  │     ├── 月牙藍
  │     └── 松針綠
  ├── 尺寸選擇（非標準 <select>）
  │     └── 30吋
  ├── 「放入購物車」按鈕（#putinCart）✅
  ├── 「立刻結帳」按鈕（#goShoppingCart）✅
  ├── 「詢問貨況 與 索取折價券」連結
  └── 「回上頁」連結
```

### 重要發現

1. **顏色/尺寸選擇器非標準 `<select>`**：
   - Day 1 以為是標準下拉選單，實際測試發現 `document.querySelector('select')` 返回 `null`
   - 推測為 ASP.NET 客製化 UI（如 `<div>` + JavaScript 模擬下拉）
   - 這增加了自動化難度：模型需要理解客製化 UI 的互動邏輯

2. **「索取折價券」非結帳折扣碼**：
   - 位於產品頁底部，屬於客服連結
   - 非結帳流程中的折扣碼輸入欄位
   - 再次確認 TravelPlus **無公開折扣碼輸入機制**

3. **會員價機制確認**：
   - 產品頁顯示「定價」與「特價」
   - 部分產品標示「會員價 : XXX」（如 NT:950）
   - 首頁 mega menu 有「現省超過 20%」「現省 45%」等分類

---

## 四、LLaMA 3.2 3B 導航決策測試

### 測試方法

給予模型以下提示：
```
你是AI電商審計代理，正在測試 https://www.travelplus.com.tw/ 網站導航。
網站資訊：
- 標題：🐴 t+樂遊家戶外旅遊專賣店
- 835 links, 7 inputs, 0 buttons, 1 form
- 任務：Navigate to a luggage product page and add to cart
請以 JSON 回應：action, target, reasoning
```

### 模型回應

```json
[
  {
    "action": "search",
    "target": "",
    "reasoning": "The website has a very large number of links, suggesting that users may need assistance finding specific products, so searching for 'luggage' is a logical first action."
  },
  {
    "action": "click",
    "target": "/product-category/luggage",
    "reasoning": "Typically, e-commerce websites have a product category dropdown or menu where users can navigate to specific categories like 'luggage'."
  }
]
```

### 評估

| 指標 | 結果 |
|------|------|
| JSON 格式 | ✅ 正確 |
| 單一明確決策 | ❌ 提供兩個選項，未明確選擇 |
| 網站結構理解 | ❌ 推測 `/product-category/luggage`，與實際 URL `HostSearchWebsite.aspx?cid=436` 不符 |
| 語言適配 | ❌ 用英文「luggage」而非中文「行李箱」搜尋 |
| 上下文利用 | ⚠️ 有用到「835 links」資訊，但未利用「7 inputs」中的搜尋框 |

**結論**：LLaMA 3.2 3B 在純文字提示下，對特定網站的 DOM 結構理解有限。需要：
1. 提供實際 DOM snapshot（HTML 片段）
2. 或提供瀏覽器截圖（多模態輸入）

---

## 五、GLM-4.7 Flash 測試

| 指標 | 數值 |
|------|------|
| 模型大小 | 19 GB (29.9B 參數, Q4_K_M) |
| 本地載入 | ✅ 成功 |
| 推論回應 | ❌ Timeout (120 秒) |

**原因推測**：
- 模型參數量大（29.9B），量化等級 Q4_K_M，本地推論需要較長時間
- 硬體資源可能不足（記憶體佔用高）
- Prompt 包含中文內容，可能增加 token 處理時間

**決定**：暫不繼續測試 GLM-4.7 Flash 本地推論，轉向雲端 API 測試。

---

## 六、TravelPlus 優惠機制完整分析

### 已確認的優惠類型

| 類型 | 位置 | 說明 |
|------|------|------|
| 會員價 | 產品頁/首頁 | 「會員價 : XXX」標示 |
| 特價 | 產品頁 | 「定價 NT:XXX（特價 : YYY）」 |
| 團購 | 首頁/分類 | 「爆款團購」區塊 |
| 分類折扣 | Mega Menu | 「現省超過 20%」「現省 45%」等 |
| 超特價 | Footer 區域 | 「約 64 折」「約 5 折」等 |

### 確認無折扣碼機制

- ❌ 結帳頁無 discount/coupon/promo code 輸入框
- ❌ 購物車頁無折扣碼欄位
- ⚠️ 「索取折價券」為客服連結，非自動折扣碼

---

## 七、模型對比（累積）

| 指標 | DeepSeek V4.1 Flash | Kimi K2.6 | LLaMA 3.2 3B |
|------|---------------------|-----------|--------------|
| **成功率** | 80% | 60% | ~40%（導航決策） |
| **平均延遲** | 1.2 秒 | 5.9 秒 | ~5 秒（本地） |
| **Token 消耗** | 2,026 | 2,091 | ~1,500 |
| **JSON 輸出** | ✅ 格式正確 | ❌ content 為空 | ✅ 格式正確 |
| **元素識別** | ✅ 正確識別 #putinCart | 無法驗證 | ❌ 推測錯誤 URL |
| **成本估算** | ~$0.0003 | ~$0.0003 | $0（本地） |

---

## 八、發現的問題或驚喜

### 🔴 問題

1. **API 金鑰限制持續**：Ollama Cloud 金鑰雖已配置，但無法確認是否有效（`***` 遮罩）。目標模型清單中 60% 仍無法測試。
2. **本地大模型推論過慢**：GLM-4.7 Flash 19GB 無法在合理時間內回應。
3. **客製化 UI 元素**：TravelPlus 的顏色/尺寸選擇器非標準 HTML `<select>`，增加自動化難度。
4. **無折扣碼機制**：CartRescue 核心價值主張（折扣碼審計）與 TravelPlus 不完全匹配。

### 🟢 驚喜

1. **Ollama API Key 已存在**：表示帳號可能已付費或可使用 Ollama Cloud。
2. **LLaMA 3.2 3B 可產出結構化 JSON**：雖然決策準確度有限，但格式輸出穩定。
3. **產品頁有明確按鈕 ID**：`#putinCart` 和 `#goShoppingCart` 仍可用於自動化測試。

---

## 九、文獻研究進度

### 今日新增重要論文

| 論文 | 來源 | 相關性 | 摘要 |
|------|------|--------|------|
| **Evaluating Open-Weight E-Commerce Agents with Environment-Grounded Verification** | arXiv:2609.16093 (2026-09-14) | ⭐⭐⭐⭐⭐ | 專門評估開源權重電商代理，提出環境接地驗證方法，與 CartRescue 本地模型測試方向高度吻合 |

### 累積文獻清單

| # | 論文 | 日期 | 狀態 |
|---|------|------|------|
| 1 | Agent A/B | 2025-04 | ✅ 已記錄 |
| 2 | From Bug Reports to Browser-Executable Procedures | 2026-08 | ✅ 已記錄 |
| 3 | Automated Web Application Testing | 2025-06 | ✅ 已記錄 |
| 4 | WebTestBench | 2026-03 | ✅ 已記錄 |
| 5 | OSWorld-Human | 2025-06 | ✅ 已記錄 |
| 6 | BEARCUBS | 2025-03 | ✅ 已記錄 |
| 7 | Building Browser Agents | 2025-11 | ✅ 已記錄 |
| 8 | A Comprehensive Survey of Multimodal LLMs | 2024-11 | ✅ 已記錄 |
| 9 | Evaluating Open-Weight E-Commerce Agents | 2026-09 | ✅ **今日新增** |

---

## 十、成本分析

### 本地模型成本

| 模型 | 成本 |
|------|------|
| LLaMA 3.2 3B | $0（本地運行） |
| GLM-4.7 Flash | $0（本地運行，但未成功） |

### Ollama Cloud 定價（待確認）

| 模型 | 狀態 |
|------|------|
| DeepSeek V4.1 Flash | 待測試 |
| Kimi K3 | 待測試 |
| GPT-OSS 120B | 待測試 |

---

## 十一、明日計畫（Day 3）

### 優先項目

1. **確認 Ollama Cloud API 有效性**：
   - 嘗試直接呼叫 Ollama Cloud API 測試金鑰是否有效
   - 若有效，測試 DeepSeek V4-pro（異常判讀）

2. **若 Cloud API 無效**：
   - 繼續本地模型測試，改用 **Qwen 2.5 7B**（較小，推論較快）
   - 測試 **Gemma 3 4B**

3. **瀏覽器自動化改進**：
   - 嘗試模擬顏色/尺寸選擇（即使非標準 `<select>`）
   - 記錄更多產品頁的 DOM 結構細節

### 待解決問題

- [ ] 確認 Ollama Cloud API 金鑰有效性
- [ ] 決定是否排除本地大模型（>10B）測試
- [ ] 調整 CartRescue 測試目標：從「折扣碼審計」轉向「會員價異常檢測」

---

## 十二、風險與對策更新

| 風險 | 影響 | 對策 |
|------|------|------|
| Ollama Cloud API 可能無效 | 無法測試雲端模型 | 先測試 API 有效性；無效則改用本地小模型 |
| 本地大模型推論過慢 | 無法在合理時間內完成測試 | 排除 >10B 本地模型，改用 3B-7B 模型 |
| TravelPlus 客製化 UI | 自動化難度增加 | 記錄更多 DOM 細節，建立專屬選擇器規則 |
| TravelPlus 無折扣碼 | 與 CartRescue 核心價值主張不匹配 | 調整測試目標為「會員價/特價異常檢測」 |

---

*Day 2 報告完成。雖然 API 限制持續，但深入分析了 TravelPlus 產品頁結構，並確認了客製化 UI 和無折扣碼機制兩個關鍵事實。*
