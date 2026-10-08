# CartRescue AI 模型實測 — Day 0 基線報告
## TravelPlus 網站分析與測試計畫啟動

> **日期**: 2026-09-17
> **測試目標網站**: https://www.travelplus.com.tw/
> **負責**: Scout（斯考特）
> **狀態**: Day 0 — 基線建立完成，明日開始模型測試

---

## 一、目標網站分析

### 網站基本資訊

| 項目 | 內容 |
|------|------|
| **網站名稱** | t+樂遊家戶外旅遊專賣店 |
| **網址** | https://www.travelplus.com.tw/ |
| **產品類別** | 戶外旅遊用品（行李箱、背包、旅行配件、旅行衣物） |
| **平台** | 自建站（ASP.NET，類似 SHOPLINE 風格） |
| **語言** | 繁體中文 |

### 網站結構圖

```
首頁 (travelplus.com.tw/)
├── 登入網站 (/login.aspx)
├── 加入會員 (/JoinMemberQuick.aspx)
├── 線上購物
│   ├── 行李箱 (/HostSearchWebsite.aspx?cid=436)
│   ├── 防搶系列 (/HostSearchWebsite.aspx?cid=437)
│   ├── 旅用配件 (/HostSearchWebsite.aspx?cid=420)
│   ├── 打理包 (/HostSearchWebsite.aspx?cid=419)
│   ├── 旅行衣物 (/HostSearchWebsite.aspx?cid=635)
│   └── 背包系列
│       ├── 登山背包 (/HostSearchWebsite.aspx?cid=621)
│       ├── 後背包 (/HostSearchWebsite.aspx?cid=445)
│       └── 側背包-腰包-斜肩包 (/HostSearchWebsite.aspx?cid=446)
└── 購物資訊
```

### 產品頁結構

**範例產品**: AZPAC 30吋 Trucker 3.0 前開行李箱
- **URL**: product.aspx?ProductColorProductID=46895
- **頁面元素**: 產品圖片、名稱、分類、規格、購買按鈕
- **購物車/結帳入口**: 「結帳前往結帳」按鈕（dropdown-toggle 類別）

### 結帳流程預估

基於網站結構，預估結帳流程：
1. 首頁 → 商品分類頁
2. 商品分類頁 → 產品頁
3. 產品頁 → 點擊「結帳前往結帳」
4. 購物車頁 → 確認商品
5. 結帳頁 → 填寫配送資訊
6. 付款頁 → 選擇付款方式（預期停止點）

---

## 二、測試環境準備

### 已就緒
- [x] 瀏覽器自動化工具（Playwright）
- [x] 截圖功能
- [x] 頁面結構分析
- [x] JavaScript 執行能力

### 待準備
- [ ] 各模型 API 金鑰與帳號
- [ ] 測試折扣碼（如有）
- [ ] 專用測試帳號（避免影響真實訂單）

---

## 三、測試模型清單與排程

### 導航模型測試（Day 1-6）

| Day | 模型 | 測試重點 |
|-----|------|---------|
| Day 1 | Gemini 2.0 Flash | 導航能力、成本基準 |
| Day 2 | GPT-4o-mini | OpenAI 輕量模型對比 |
| Day 3 | Gemini 3.1 Flash | Google 最新世代 |
| Day 4 | DeepSeek V4.1 Flash | 開源低價替代 |
| Day 5 | Kimi K2.6 | 亞太地區延遲優勢 |
| Day 6 | Claude 3.5 Haiku | Anthropic 快速模型 |

### 異常判讀模型測試（Day 7-12）

| Day | 模型 | 測試重點 |
|-----|------|---------|
| Day 7 | Claude Sonnet 5 (Intro) | 最新 Sonnet，性價比 |
| Day 8 | Claude Opus 4.8 | Computer Use 之王 |
| Day 9 | Gemini 3.1 Pro | Google 最強 |
| Day 10 | GPT-4o | OpenAI 旗艦 |
| Day 11 | Kimi K3 | Moonshot 旗艦 |
| Day 12 | GPT-5.5 | OpenAI 最新頂規 |

### 混合路由測試（Day 13-15）

| Day | 路由組合 | 測試重點 |
|-----|---------|---------|
| Day 13 | Flash + Sonnet 5 | 推薦組合實測 |
| Day 14 | 3.1 Flash + Sonnet 5 | 升級組合 |
| Day 15 | 全旗艦對比 | 成本效益驗證 |

---

## 四、測試指標定義

### 導航能力指標
1. **成功率**: 完成從首頁到付款頁的步驟比例（%）
2. **步驟效率**: 實際步驟數 / 預期步驟數
3. **時間**: 從首頁到付款頁總耗時（秒）
4. **錯誤類型**: 點擊錯誤、選擇器失效、頁面未載入等

### 異常判讀指標
1. **準確率**: 正確識別異常的比例（%）
2. **誤報率**: 無異常但報錯的比例（%）
3. **漏報率**: 有異常但未報的比例（%）
4. **信心分數**: 模型對判斷的確信程度

### 成本指標
1. **Input tokens**: 每次呼叫的輸入 token 數
2. **Output tokens**: 每次呼叫的輸出 token 數
3. **單次成本**: 單次審計的 API 費用（USD）
4. **延遲**: API 回應時間（TTFT + 總時間）

---

## 五、文獻研究進度

### 已找到相關論文

| 論文 | 來源 | 相關性 |
|------|------|--------|
| Agent A/B: Automated Web A/B Testing with LLM Agents | arxiv:2504.09723 | ⭐⭐⭐ 高 |
| From Bug Reports to Browser-Executable Procedures | arxiv:2608.03598 | ⭐⭐⭐ 高 |
| Automated Web Application Testing: End-to-End Test Case | arxiv:2506.02529 | ⭐⭐⭐ 高 |
| A Comprehensive Survey of Multimodal LLMs | arxiv:2411.06284 | ⭐⭐ 中 |
| Multimodal Fusion and Vision-Language Models | arxiv:2504.02477 | ⭐⭐ 中 |

### 待搜尋方向
- [ ] Stagehand / Browser Use / Skyvern 官方 benchmark
- [ ] OSWorld / Mind2Web 電腦使用基準測試
- [ ] Noibu 技術白皮書（如有公開）
- [ ] 電商棄單率最新研究（Baymard 2026）

---

## 六、風險與對策

| 風險 | 對策 |
|------|------|
| 網站改版導致測試失效 | 每日測試前確認網站結構，記錄版本 |
| API 金鑰不足/用完 | 優先測試低成本模型，高成本模型用 sample size |
| 測試產生假訂單 | 在付款頁停止，不提交訂單 |
| 網站阻擋自動化瀏覽器 | 調整 User-Agent，必要時聯繫網站取得授權 |
| 模型延遲影響測試時間 | 記錄實際延遲，納入成本模型 |

---

## 七、下一步

### 明天（Day 1）計畫
- [ ] 測試 Gemini 2.0 Flash 導航能力
- [ ] 記錄成功率、時間、成本
- [ ] 搜尋更多相關論文
- [ ] 撰寫 Day 1 報告

### 自動化機制
- **每日早上 9 點**: 自動執行測試並回報老闆
- **Cron Job ID**: `5781fd01e15a`
- **連續性**: 已啟用（記住上次進度）

---

*Day 0 基線報告完成。明日開始正式模型測試。*
