# CartRescue AI — 長期任務執行計畫

> **日期**: 2026-10-08
> **負責**: Scout（斯考特）
> **執行方式**: delegate_task 子代理並行執行
> **回報頻率**: 每日進度

---

## 已建立長期任務

老闆指示「自行決定，列為長期任務」後，我已建立 **4 個並行子代理任務**，涵蓋當前最優先行動：

### 任務一：價格提取邏輯增強（task-price-extraction）

| 項目 | 內容 |
|------|------|
| **目標** | 讓規則引擎正則表達式支援全球電商的價格格式 |
| **範圍** | NT$ / TWD / $ / € / ¥ / Price: xxx / 純數字等 |
| **產出** | `src/price_extractor.py`（獨立模組）+ 單元測試 |
| **終止條件** | 通過 20+ 種格式測試， TravelPlus 實測可提取價格 |
| **預估時間** | 4–6 小時 |

### 任務二：Shopify 測試商店完整結帳驗證（task-shopify-checkout）

| 項目 | 內容 |
|------|------|
| **目標** | 用無登入牆的 Shopify 商店驗證所有 10 條規則 |
| **流程** | 產品頁 → 加入購物車 → 折扣碼輸入 → 結帳頁 → 異常檢測 |
| **產出** | `research/SHOPIFY_THREE_LAYER_TEST.md` + 測試腳本 |
| **終止條件** | 覆蓋 RULE-001 到 RULE-007（折扣計算、失效、超時、錯誤、價格不一致、元素消失、缺貨）|
| **預估時間** | 6–8 小時 |

### 任務三：TravelPlus 測試帳號申請與深度測試（task-travelplus-account）

| 項目 | 內容 |
|------|------|
| **目標** | 取得測試帳號，解鎖會員專屬結帳流程的完整測試 |
| **流程** | 1. 聯繫 TravelPlus 客服 → 2. 申請測試帳號 → 3. 登入後完整跑結帳流程 → 4. 驗證折扣碼輸入與計算 |
| **產出** | 測試帳號憑證 + `research/TRAVELPLUS_FULL_CHECKOUT_TEST.md` |
| **終止條件** | 成功登入並完成一次含折扣碼的結帳流程審計 |
| **預估時間** | 1–3 天（取決於 TravelPlus 回應速度）|

### 任務四：Supabase + LINE 警報串接（task-alert-integration）

| 項目 | 內容 |
|------|------|
| **目標** | 建立異常結果儲存與即時推播機制 |
| **技術** | Supabase (PostgreSQL) + LINE Messaging API |
| **流程** | 1. 設計 anomalies 資料表 → 2. 撰寫儲存函數 → 3. 串接 LINE push API → 4. 測試 Critical 異常推播 |
| **產出** | `src/alert_service.py` + Supabase schema + LINE webhook handler |
| **終止條件** | 單次審計產生 Critical 異常後，10 秒內收到 LINE 通知 |
| **預估時間** | 8–12 小時 |

---

## 任務依賴關係

```
任務一（價格提取）    任務四（警報串接）
      ↓                    ↓
任務二（Shopify 測試） ←──┘
      ↓
任務三（TravelPlus 深度）
```

- 任務一與任務四可**完全並行**
- 任務二可獨立開始（即使價格提取未完成，Shopify 測試可用現有邏輯）
- 任務三需等 TravelPlus 回覆，與其他任務並行進行

---

## 每日回報內容

每個子代理將於完成時或每日回報：

1. **完成進度 %**
2. **已解決的問題**
3. **遇到的 blocker**
4. **產出檔案路徑**
5. **是否需要老闆決策**

---

## 預期總產出

| 產出 | 說明 |
|------|------|
| `src/price_extractor.py` | 全球價格格式提取模組 |
| `research/SHOPIFY_THREE_LAYER_TEST.md` | Shopify 完整結帳測試報告 |
| `research/TRAVELPLUS_FULL_CHECKOUT_TEST.md` | TravelPlus 深度測試報告 |
| `src/alert_service.py` | Supabase + LINE 警報服務 |
| `docs/supabase_schema.sql` | anomalies 資料表結構 |

---

## 執行狀態

| 任務 | 狀態 | 開始時間 |
|------|------|---------|
| task-price-extraction | 🟡 pending | 等待委派 |
| task-shopify-checkout | 🟡 pending | 等待委派 |
| task-travelplus-account | 🟡 pending | 等待委派 |
| task-alert-integration | 🟡 pending | 等待委派 |

---

*文件由 CartRescue AI Scout AI 引擎自動生成。*
*計畫建立時間: 2026-10-08 11:15 CST*
