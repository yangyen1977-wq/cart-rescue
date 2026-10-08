# TravelPlus 模型每日測試報告 Day 20（2026-10-07）

## 當日測試模型

| 模型 | 類型 | 測試項目 | 狀態 |
|------|------|---------|------|
| **Kimi K3（Ollama Cloud）** | 異常判讀 | 折扣計算、風險評級、結構化報告 | ✅ 完成 |
| **DeepSeek V4.1 Flash（Ollama Cloud）** | 導航 + 異常判讀 | 折扣計算、導航流程規劃 | ✅ 完成 |

> **模型取得方式**：兩者皆透過 Ollama Cloud OpenAI-compatible API（`https://ollama.com/v1`）呼叫，使用 `OLLAMA_API_KEY` 認證。

---

## 一、網站結構分析（travelplus.com.tw）

### 1.1 首頁掃描

| 項目 | 結果 |
|------|------|
| 網站標題 | 🐴 t+樂遊家戶外旅遊專賣店 首頁 |
| HTML 大小 | ~627KB |
| 總連結數 | 319 |
| 商品連結 | 0（首頁無直接商品連結，皆為分類頁） |

**導航結構**：
- 頂層：會員服務、前往結帳、登入網站、加入會員、線上購物
- 一級分類：出國旅行、背包、男性服飾、女性服飾、鞋子
- 二級分類（出國旅行）：行李箱 (cid=436)、防搶系列 (cid=437)、旅用配件 (cid=420)、打理包 (cid=419)、旅行衣物 (cid=635)
- 二級分類（背包）：自助旅行 (cid=444)、登山背包 (cid=621)、後背包 (cid=445)、側背包-腰包-斜肩包 (cid=446)、攝影包 (cid=447)

### 1.2 行李箱分類頁（cid=436）批量擷取

使用 `curl` + regex 從分類頁提取 **6 筆產品價格**（SSR 網站，HTML 含完整價格資訊）：

| # | 產品名稱 | 定價 | 特價 | 實際折扣 | 標示折扣 |
|---|---------|------|------|---------|---------|
| 1 | Venturesafe G3 探險防盜雙肩背包(15L) | NT$4,680 | NT$2,980 | **6.4 折** | 約64折 |
| 2 | 女 Vana 圓領抗UV短袖排汗衣 | NT$850 | NT$680 | **8.0 折** | 約8折 |
| 3 | Roamers 漫遊休閒後背包(18L) | NT$2,880 | NT$1,440 | **5.0 折** | 無 |
| 4 | 超輕三節式健行登山杖(2入) | NT$3,760 | NT$2,480 | **6.6 折** | 無 |
| 5 | Venturesafe G3 探險防盜雙肩後背包(28L) | NT$5,980 | NT$3,980 | **6.7 折** | 無 |
| 6 | 抗UV遮陽休閒帽(臉/肩頸部防曬設計) | NT$850 | NT$590 | **6.9 折** | 無 |

> ⚠️ **發現**：第 3 項（Roamers 背包）實際為 **5 折（50% off）**，但頁面未標示任何折扣資訊。對消費者而言，無法直觀得知這是半價商品，屬於「隱藏折扣」情境。

---

## 二、Kimi K3 測試結果

### 測試 1：折扣異常判讀（有標示折扣）

**Prompt**：產品定價 NT$4680、特價 NT$2980、標示約64折，要求計算實際折扣率並判斷是否一致。

**結果**：
- ✅ **計算正確**：2980 ÷ 4680 = 0.6368 → 約 63.7%，即約 **6.37 折**
- ✅ **判斷正確**：標示「約64折」與實際 6.37 折一致（差異 0.3%，在合理四捨五入範圍內）
- ✅ **風險評級**：Low（低風險）
- ✅ **輸出格式**：遵循要求的四段式結構（計算過程 → 標示折扣 → 是否一致 → 風險等級）

**Token 消耗**：
- Prompt: 297 tokens
- Completion: 800 tokens
- **Total: 1,097 tokens**
- **耗時：8,372 ms**

**問題**：Completion 全部用於 `reasoning` 欄位，但 `content` 欄位只輸出了報告的前半段（到「標示折扣率」就截斷）。這表示 **max_tokens=800 對 Kimi K3 不足**——該模型把大量 token 用於內部推理，導致正式輸出被截斷。

### 測試 2：折扣異常判讀（無標示折扣）

**Prompt**：產品定價 NT$2880、特價 NT$1440、無標示折扣。

**結果**：
- ✅ **計算正確**：1440 ÷ 2880 = 0.5 → **5 折**
- ⚠️ **風險評級**：標為「中高風險」，理由是「50% off 為深度折扣但未標示，可能涉及虛高原價或價格欺詐」。這個判斷**過於保守**——未標示折扣不等於價格異常，可能只是促銷策略不同。
- ⚠️ **輸出截斷**：同樣因 max_tokens=800 限制，content 在「異常觀」處截斷。

**Token 消耗**：1,038 tokens | **耗時：10,778 ms**

### 測試 3：導航流程規劃

**Prompt**：根據 TravelPlus 首頁結構，規劃從首頁到結帳的最少步驟。

**結果**：
- ❌ **Content 完全為空**：所有 800 completion tokens 全用於 `reasoning`
- Reasoning 內容正確描述了 7 步流程（首頁→分類→商品→加入購物車→前往結帳→登入→填寫資料→確認）
- **結論**：Kimi K3 在 Ollama Cloud 上的實作似乎把推理內容放在 `reasoning` 欄位，但由於 max_tokens 限制，導致 `content` 為空。這是一個**輸出格式問題**，可能與 Ollama Cloud 的推理欄位處理有關。

**Token 消耗**：1,134 tokens | **耗時：8,392 ms**

### Kimi K3 總評

| 指標 | 結果 |
|------|------|
| 計算正確率 | 100%（2/2） |
| 折扣語義理解 | ✅ 正確理解「幾折 = 售價÷定價×10」 |
| 風險判斷準確度 | ⚠️ 測試 2 過度保守（無標示折扣≠高風險） |
| Content 輸出穩定性 | ❌ 3/3 測試出現截斷或空內容 |
| 平均耗時 | ~9.2 秒/請求 |
| 平均 Token | ~1,090 tokens/請求 |

---

## 三、DeepSeek V4.1 Flash 測試結果

### 測試 4：折扣異常判讀（對照組）

**Prompt**：與測試 1 相同（定價4680、特價2980、標示約64折）。

**結果**：
- ✅ **計算正確**：2980 ÷ 4680 ≈ 63.68% → **約6.37折**
- ✅ **判斷精準**：「標示『約64折』合理，實際還比64折便宜約 NT$15」
- ✅ **風險評級**：Low（低風險）
- ✅ **輸出完整**：Content 有實際內容（非空），簡潔三行回答

**Token 消耗**：695 tokens | **耗時：3,372 ms**

### 測試 5：導航流程規劃（對照組）

**Prompt**：與測試 3 相同。

**結果**：
- ⚠️ **Content 同樣為空**：所有 completion tokens 用於 `reasoning`
- Reasoning 內容正確，分析了最少步徑的兩種情境（購物車已有商品 vs 空購物車）
- **結論**：這不是 Kimi K3 獨有的問題——**DeepSeek V4.1 Flash 在 Ollama Cloud 上也出現 content 為空**。

**Token 消耗**：941 tokens | **耗時：3,873 ms**

### DeepSeek V4.1 Flash 總評

| 指標 | 結果 |
|------|------|
| 計算正確率 | 100%（1/1） |
| 輸出簡潔度 | ✅ 優於 Kimi K3（簡潔三行 vs 冗長報告） |
| Content 輸出穩定性 | ⚠️ 導航測試同樣為空 |
| 速度 | ✅ 明顯快於 Kimi K3（3.4s vs 8.4s） |
| Token 效率 | ✅ 更省 token（695 vs 1097） |

---

## 四、兩模型對比總結

| 比較項目 | Kimi K3 | DeepSeek V4.1 Flash | 勝者 |
|---------|---------|---------------------|------|
| 折扣計算正確性 | ✅ | ✅ | 平手 |
| 輸出簡潔度 | ❌ 冗長 | ✅ 精簡 | **DeepSeek** |
| 風險判斷合理性 | ⚠️ 過度保守 | ✅ 精準 | **DeepSeek** |
| 回應速度 | ~9.2s | ~3.4s | **DeepSeek** |
| Token 效率 | ~1,090 tokens | ~818 tokens | **DeepSeek** |
| Content 穩定性 | ❌ 3/3 截斷/空值 | ⚠️ 1/2 空值 | **DeepSeek** |
| 繁體中文輸出 | ✅ 良好 | ⚠️ 簡體為主 | **Kimi K3** |

**綜合評價**：
- **DeepSeek V4.1 Flash** 在速度、token 效率、輸出簡潔度上全面優於 Kimi K3，適合做 CartRescue 的**輔助分析模型**（report generation）。
- **Kimi K3** 的繁體中文表達更自然，但存在嚴重的輸出截斷問題——在 Ollama Cloud 上需要把 `max_tokens` 設到 1200-1500 以上才能獲得完整輸出。
- **重大發現**：兩個模型在 Ollama Cloud 上的「導航流程規劃」測試都產生空的 `content`——這暗示 Ollama Cloud 對 `reasoning` 欄位的處理可能有問題，導致當模型產生推理內容時，正式輸出被擠壓為空。

---

## 五、發現的問題與驚喜

### 🔴 問題

1. **Ollama Cloud「空 Content」Bug**：Kimi K3 和 DeepSeek V4.1 Flash 在 Ollama Cloud 上，當模型產生 reasoning 內容時，`content` 欄位經常為空或被截斷。這可能是 Ollama Cloud 對 reasoning-enabled models 的輸出格式處理問題。

2. **Kimi K3 風險過度保守**：對於「無標示折扣」的情境，Kimi K3 直接評為「中高風險」，但這只是促銷策略差異（有些商家不標折扣%，只在價格上體現），不等同於價格異常。

3. **TravelPlus 產品頁 vs 列表頁價格差異**：列表頁顯示「定價4680→特價2980」，但產品詳情頁顯示「定價4680→特價3854→會員價3132」。這**可能是不同產品混雜**（列表頁抓到了相關商品的價格），但也可能是列表頁與詳情頁促銷不同步。需要進一步驗證。

### 🟢 驚喜

1. **DeepSeek V4.1 Flash 計算精準**：不僅算出 6.37 折，還進一步指出「實際比64折便宜約 NT$15」——這是**細節級的精確度**，對審計很有價值。

2. **curl + regex 批量提取穩定**：今日成功從行李箱分類頁提取 6 筆產品價格，SSR 架構確實適合無瀏覽器優先策略。

---

## 六、文獻研究（新增 4 篇，累積 48 篇）

### arXiv:2503.23350 — A Survey of WebAgents: Towards Next-Generation AI Agents for Web Automation with Large Foundation Models
- **日期**：2025-03-30
- **與 CartRescue 相關性**：⭐⭐⭐⭐⭐
- **核心貢獻**：系統性回顧 LLM-based Web Agent 的技術架構（感知→推理→行動）、評估基準與挑戰
- **與今日測試直接對照**：
  - 論文提到 Web Agent 面臨「輸出格式不穩定」問題——與今日 Kimi K3 / DeepSeek 的「空 Content」現象完全吻合
  - 建議使用結構化輸出（JSON mode / function calling）提升穩定性

### arXiv:2508.02630 — What Is Your AI Agent Buying? Evaluation, Biases, Model Selection and Inference in ACES
- **日期**：2025-08-04
- **與 CartRescue 相關性**：⭐⭐⭐⭐
- **核心貢獻**：ACES 框架——用於審計 AI Agent 的決策行為，發現 Agent 存在「選擇同質性」（choice homogeneity）偏差
- **與 CartRescue 對照**：ACES 框架可直接借鑑用於 CartRescue 的「折扣審計」場景——我們不只是審計網站，也要審計 AI 模型自身的判斷偏差

### arXiv:2508.15832 — A Functionality-Ground Benchmark for Evaluating Web Agents in E-commerce Domains
- **日期**：2025-08-18
- **與 CartRescue 相關性**：⭐⭐⭐⭐⭐
- **核心貢獻**：電商領域 Web Agent 的功能性評估基準——涵蓋商品搜尋、比價、庫存檢查、結帳流程
- **與 CartRescue 對照**：CartRescue 可以參考此基準設計自身的「結帳審計」測試案例集

### arXiv:2508.13024 — WebMall: A Multi-Shop Benchmark for Evaluating Web Agents
- **日期**：2025-08-18
- **與 CartRescue 相關性**：⭐⭐⭐⭐
- **核心貢獻**：首個離線多商店基準，用於評估 Web Agent 在跨店比價任務上的表現
- **與 CartRescue 對照**：CartRescue 的核心價值正是「跨網站比價審計」——WebMall 提供了評估方法論

---

## 七、明日計畫（Day 21）

1. **Ollama Cloud 空 Content 問題排查**：測試 `max_tokens=1500` 是否能解決 Kimi K3 / DeepSeek 的輸出截斷問題；嘗試關閉 reasoning 或改用不同 prompt 格式
2. **結構化輸出測試**：改用 JSON mode / function calling 測試模型穩定性（參考 arXiv:2503.23350 的建議）
3. **多產品批次審計**：對今日提取的 6 筆產品，讓模型同時分析多筆折扣，測試批量處理能力
4. **規則引擎對照**：用 Python 純規則計算折扣率，與 LLM 結果比對，量化 LLM 的「幻覺率」

---

## 八、需要老闆決定的事項

1. **Ollama Cloud vs 原生 API**：Ollama Cloud 上的 Kimi K3 和 DeepSeek 都出現「reasoning 擠壓 content」的問題。是否需要測試 Moonshot（Kimi）和 DeepSeek 的原生 API，以確認是 Ollama Cloud 的中介層問題還是模型本身問題？

2. **異常判讀模型的風險閾值**：Kimi K3 對「無標示折扣」評為「中高風險」，DeepSeek 則較為理性。CartRescue 的風險評級標準應由人類審計師定義，而非完全交給 LLM——是否需要 Scout 撰寫一份「風險評級規則書」（如：無標示折扣=Medium，標示與實際差異>5%=High）？

---

*報告產生時間：2026-10-07 09:00 CST*  
*執行者：Scout（斯考特）| CartRescue AI*  
*累積測試天數：20 天 | 累積文獻：48 篇*
