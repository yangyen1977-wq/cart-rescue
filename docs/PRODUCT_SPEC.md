# CartRescue AI — 產品規格書（PRD）
**文件版本**：v1.0  
**日期**：2026-09-17  
**負責人**：Scout（CartRescue AI AI 執行引擎）  
**老闆**：Vincent

---

## 目錄
1. [產品願景與範圍](#產品願景與範圍)
2. [MVP 功能清單（Phase 1）](#mvp-功能清單phase-1)
3. [長期功能清單（Phase 2-3）](#長期功能清單phase-2-3)
4. [技術架構規格](#技術架構規格)
5. [API 設計](#api-設計)
6. [審計流程定義](#審計流程定義)
7. [安全與合規規格](#安全與合規規格)
8. [效能目標](#效能目標)
9. [風險與假設](#風險與假設)

---

## 產品願景與範圍

### 產品願景
> 讓電商不再因為「網站壞掉而不知道」而損失收入。CartRescue AI 是電商專用的 AI 巡檢員，每天自動模擬真實購物流程，在客戶發現問題之前先發現、先警報、先修復。

### 目標用戶
- **Primary**：電商營運經理 / 數位行銷主管（需即時知道結帳是否正常）
- **Secondary**：電商技術團隊 / DevOps（需快速定位問題根因）
- **Tertiary**：品牌創辦人 / 電商創業者（無技術背景，需簡單儀表板）

### 產品範圍
- **In Scope**：
  - 電商網站購物流程巡檢（瀏覽 → 加購物車 → 應用折扣 → 結帳 → 支付頁）
  - 折扣碼有效性驗證
  - 結帳流程異常檢測與警報
  - AI 判斷異常並生成可執行修復建議
  - n8n 自動化工作流觸發修復
  - 儀表板與報告
- **Out of Scope（Phase 1）**：
  - 真實用戶行為分析（非 replay，是模擬）
  - 性能/速度監控（專注功能正確性）
  - 多語言電商支援（Phase 2）
  - Mobile App 巡檢（Phase 3）

---

## MVP 功能清單（Phase 1）

### 1. 巡檢引擎（Audit Engine）
| ID | 功能 | 說明 | 優先級 |
|----|------|------|--------|
| A1 | 購物流程模擬 | 使用 Stagehand + Playwright 模擬完整購物流程 | P0 |
| A2 | 折扣碼驗證 | 輸入測試折扣碼，驗證是否正確計算折扣 | P0 |
| A3 | 結帳頁面檢查 | 確認結帳表單可填寫、總金額正確 | P0 |
| A4 | 支付頁面到達 | 驗證能到達最終支付頁面（不實際付款） | P0 |
| A5 | 多平台模板 | 預設 Shopify、WooCommerce、Magento 模板 | P1 |
| A6 | 自定義流程 | 用戶可定義自己的巡檢步驟 | P1 |

### 2. AI 判斷引擎（AI Judgment Engine）
| ID | 功能 | 說明 | 優先級 |
|----|------|------|--------|
| B1 | LLM 異常判斷 | 將頁面截圖 + DOM 輸入 LLM，判斷是否異常 | P0 |
| B2 | 信心分數計算 | 輸出 0-100 的信心分數 | P0 |
| B3 | 異常分類 | 自動分類：折扣失效、結帳錯誤、頁面崩潰等 | P0 |
| B4 | 修復建議生成 | 生成自然語言修復步驟 | P1 |
| B5 | 歷史比對 | 與歷史正常狀態比對，偵測回歸 | P1 |

### 3. 警報與通知（Alerting）
| ID | 功能 | 說明 | 優先級 |
|----|------|------|--------|
| C1 | 即時警報 | 信心分數低於閾值時觸發 | P0 |
| C2 | 多通道通知 | Slack / Email / Discord / Webhook | P0 |
| C3 | 警報分級 | Critical / Warning / Info 三級 | P1 |
| C4 | 警報抑制 | 相同問題不重複警報（分鐘級冷卻） | P1 |

### 4. 自動修復（Auto-Remediation via n8n）
| ID | 功能 | 說明 | 優先級 |
|----|------|------|--------|
| D1 | n8n Webhook 觸發 | 異常時發送 webhook 到 n8n | P0 |
| D2 | 折扣碼自動下架 | 失效時自動從 Shopify 下架折扣碼 | P1 |
| D3 | 修復結果回寫 | n8n 執行結果回傳 CartRescue 記錄 | P1 |
| D4 | 修復建議模板 | 預設常見修復 n8n workflow 模板 | P2 |

### 5. 儀表板與報告（Dashboard）
| ID | 功能 | 說明 | 優先級 |
|----|------|------|--------|
| E1 | 巡檢狀態總覽 | 所有網站的即時健康狀態 | P0 |
| E2 | 異常歷史記錄 | 可搜尋、可篩選的異常列表 | P0 |
| E3 | 截圖與 DOM 查看 | 異發生時的截圖與 DOM 結構 | P0 |
| E4 | 每週報告 | 自動生成健康檢查報告 | P2 |
| E5 | 收入影響預估 | 根據異常推算潛在收入損失 | P2 |

---

## 長期功能清單（Phase 2-3）

### Phase 2（3-6 個月）
- **多語言支援**：日文、韓文、東南亞電商平台
- **A/B 測試整合**：巡檢不同版本頁面
- **競品折扣碼監控**：監控競爭對手的促銷策略
- **API 測試**：後端 API 端點直接測試
- **團隊權限管理**：RBAC（角色權限控制）
- **SSO / SAML**：企業級身份驗證
- **CI/CD 整合**：GitHub Actions、GitLab CI 插件

### Phase 3（6-12 個月）
- **Mobile App 巡檢**：Appium / Maestro 模擬手機購物流程
- **視覺回歸測試**：像素級 UI 差異比對
- **智能排程**：根據流量高峰自動調整巡檢頻率
- **預測性維護**：基於歷史數據預測何時可能出問題
- **白標方案**：代理商可貼牌銷售
- **Marketplace**：n8n workflow 市集，用戶分享修復模板

---

## 技術架構規格

### 系統架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        CartRescue AI Platform                  │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Dashboard)    │  API Gateway (FastAPI)                │
│  - Next.js 14 + shadcn  │  - Auth / Rate Limit / Routing        │
│  - Real-time WebSocket   │                                       │
├─────────────────────────────────────────────────────────────────┤
│  Audit Engine            │  AI Judgment Engine                   │
│  - Stagehand (AI browser)│  - LLM Router (OpenAI / Claude / Local)│
│  - Playwright            │  - Prompt Template Manager            │
│  - Proxy Rotation        │  - Confidence Scorer                    │
│  - Screenshot Capture    │  - Anomaly Classifier                 │
├─────────────────────────────────────────────────────────────────┤
│  Workflow Engine         │  Data Layer                           │
│  - n8n (Self-hosted)     │  - Supabase (Postgres + Auth)         │
│  - Webhook Receiver      │  - Storage: Audit Logs / Screenshots  │
│  - Auto-remediation      │  - Redis: Job Queue / Cache           │
├─────────────────────────────────────────────────────────────────┤
│  Infrastructure                                                │
│  - Docker / Docker Compose (MVP)                                │
│  - Kubernetes (Scale)                                          │
│  - Cloudflare R2 (Screenshot Storage)                           │
└─────────────────────────────────────────────────────────────────┘
```

### 核心技術棧
| 層級 | 技術 | 用途 |
|------|------|------|
| 前端 | Next.js 14 + TypeScript + Tailwind + shadcn/ui | 儀表板 |
| API | FastAPI (Python) | REST API |
| 瀏覽器自動化 | Stagehand + Playwright | 模擬購物流程 |
| AI/LLM | OpenAI GPT-4o / Claude 3.5 Sonnet / Local LLM | 異常判斷 |
| 工作流 | n8n (self-hosted) | 自動修復 |
| 資料庫 | Supabase (PostgreSQL) | 主資料庫 |
| 快取/佇列 | Redis | 任務佇列、快取 |
| 儲存 | Cloudflare R2 / AWS S3 | 截圖與 DOM |
| 代理 | Bright Data / Oxylabs | IP 輪替 |

### LLM Router 設計
```python
class LLMRouter:
    """
    根據任務類型與成本優先級選擇最適合的 LLM
    """
    def route(self, task: Task) -> LLMProvider:
        if task.criticality == "high" and task.requires_vision:
            return Claude35Sonnet()  # 最佳視覺理解
        elif task.criticality == "high":
            return GPT4o()           # 最佳推理
        elif task.is_batch:
            return LocalLLM()        # 成本最低
        else:
            return GPT4oMini()       # 平衡性價比
```

### 資料模型（核心）
```sql
-- 網站設定
CREATE TABLE websites (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    platform TEXT CHECK (platform IN ('shopify', 'woocommerce', 'magento', 'custom')),
    checkout_steps JSONB,          -- 自定義結帳步驟
    discount_codes TEXT[],         -- 測試用折扣碼
    test_sku TEXT,                 -- 測試商品 SKU
    ip_whitelist TEXT[],           -- IP 白名單
    alert_threshold INT DEFAULT 70, -- 信心分數閾值
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 巡檢任務
CREATE TABLE audit_runs (
    id UUID PRIMARY KEY,
    website_id UUID REFERENCES websites,
    status TEXT CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    screenshot_url TEXT,
    dom_snapshot_url TEXT,
    confidence_score INT,          -- 0-100
    anomaly_detected BOOLEAN,
    anomaly_type TEXT,
    remediation_triggered BOOLEAN,
    remediation_result JSONB
);

-- 異常記錄
CREATE TABLE anomalies (
    id UUID PRIMARY KEY,
    audit_run_id UUID REFERENCES audit_runs,
    website_id UUID REFERENCES websites,
    type TEXT,                     -- discount_failed, checkout_error, etc.
    severity TEXT CHECK (severity IN ('critical', 'warning', 'info')),
    description TEXT,
    confidence INT,
    screenshot_url TEXT,
    suggested_fix TEXT,
    fixed_at TIMESTAMPTZ,
    fix_method TEXT                -- manual, n8n_auto, etc.
);
```

---

## API 設計

### 認證
- **方式**：Bearer Token（JWT）
- **來源**：Supabase Auth
- **權限**：基於用戶角色的 API 訪問控制

### API 端點

#### 1. 網站管理
```http
POST /api/v1/websites
Content-Type: application/json
Authorization: Bearer {jwt}

{
  "name": "My Shopify Store",
  "url": "https://my-store.myshopify.com",
  "platform": "shopify",
  "discount_codes": ["TEST10", "SUMMER20"],
  "test_sku": "test-product-001",
  "checkout_steps": [
    {"action": "goto", "url": "/products/test-product-001"},
    {"action": "click", "selector": "[data-add-to-cart]"},
    {"action": "goto", "url": "/checkout"},
    {"action": "fill", "selector": "#discount-code", "value": "TEST10"},
    {"action": "click", "selector": "[data-apply-discount]"},
    {"action": "verify", "type": "discount_applied"}
  ],
  "alert_threshold": 70
}

Response 201:
{
  "id": "uuid",
  "status": "created",
  "next_audit_scheduled": "2026-09-17T12:00:00Z"
}
```

#### 2. 觸發巡檢
```http
POST /api/v1/websites/{id}/audit
Authorization: Bearer {jwt}

Response 202:
{
  "audit_run_id": "uuid",
  "status": "pending",
  "estimated_completion": "2026-09-17T12:05:00Z"
}
```

#### 3. 取得巡檢結果
```http
GET /api/v1/audit-runs/{audit_run_id}
Authorization: Bearer {jwt}

Response 200:
{
  "id": "uuid",
  "website_id": "uuid",
  "status": "completed",
  "confidence_score": 45,
  "anomaly_detected": true,
  "anomaly": {
    "type": "discount_failed",
    "severity": "critical",
    "description": "Discount code 'SUMMER20' returned 'Code not found' error",
    "screenshot_url": "https://r2.cartrescue.ai/screenshots/uuid.png",
    "dom_snapshot_url": "https://r2.cartrescue.ai/dom/uuid.json",
    "suggested_fix": "Check if discount code SUMMER20 is still active in Shopify admin."
  },
  "remediation": {
    "triggered": true,
    "n8n_workflow_id": "workflow-uuid",
    "status": "completed",
    "result": "Discount code deactivated successfully"
  },
  "started_at": "2026-09-17T12:00:00Z",
  "completed_at": "2026-09-17T12:03:45Z"
}
```

#### 4. 異常列表
```http
GET /api/v1/anomalies?website_id={id}&severity=critical&from=2026-09-01&to=2026-09-17
Authorization: Bearer {jwt}

Response 200:
{
  "total": 42,
  "page": 1,
  "per_page": 20,
  "anomalies": [
    {
      "id": "uuid",
      "type": "checkout_error",
      "severity": "critical",
      "description": "Payment gateway timeout after 30s",
      "confidence": 92,
      "detected_at": "2026-09-17T08:30:00Z",
      "fixed_at": null
    }
  ]
}
```

#### 5. Webhook（n8n 回調）
```http
POST /api/v1/webhooks/n8n/remediation
Content-Type: application/json
X-Signature: {hmac-sha256}

{
  "audit_run_id": "uuid",
  "workflow_id": "n8n-workflow-uuid",
  "status": "success",
  "result": {
    "action": "discount_deactivated",
    "code": "SUMMER20",
    "shopify_response": "OK"
  },
  "executed_at": "2026-09-17T12:04:00Z"
}

Response 200: {"status": "recorded"}
```

---

## 審計流程定義

### 標準購物流程步驟

```
Step 1: 訪問商品頁
  ├─ Action: goto /products/{test_sku}
  ├─ Verify: 頁面 HTTP 200，商品名稱正確載入
  └─ Timeout: 30s

Step 2: 加入購物車
  ├─ Action: click [data-add-to-cart]
  ├─ Verify: 購物車數量 +1，出現「Added」提示
  └─ Timeout: 10s

Step 3: 前往結帳
  ├─ Action: goto /checkout
  ├─ Verify: 結帳頁面載入，顯示商品與價格
  └─ Timeout: 30s

Step 4: 輸入折扣碼
  ├─ Action: fill #discount-code with {discount_code}
  ├─ Action: click [data-apply-discount]
  ├─ Verify: 總金額正確減去折扣，無錯誤訊息
  └─ Timeout: 15s

Step 5: 填寫運送資訊（測試用假資料）
  ├─ Action: fill 運送表單 with test data
  ├─ Verify: 表單驗證通過
  └─ Timeout: 20s

Step 6: 前往支付頁
  ├─ Action: click [data-continue-to-payment]
  ├─ Verify: 到達支付頁面，顯示支付選項
  ├─ IMPORTANT: 不填寫真實信用卡，不點擊最終付款
  └─ Timeout: 20s

Step 7: AI 判斷
  ├─ Input: 所有步驟截圖 + DOM + 錯誤日誌
  ├─ LLM Prompt: "請判斷以上購物流程是否正常完成..."
  └─ Output: 信心分數 + 異常描述 + 修復建議
```

### 異常判斷標準

> **📚 論文佐證**：以下判斷標準基於 46 篇 arXiv 論文研究，特別是 WebTestPilot (2602.11724) 的「符號化 GUI 元素斷言」與 HxAgent (2608.15491) 的「每步狀態評估器」方法論。

| 異常類型 | 觸發條件 | 嚴重度 | 論文依據 |
|----------|----------|--------|---------|
| `discount_failed` | 折扣碼應用後金額未變，或出現錯誤訊息 | Critical | WebTestPilot: 需驗證「總金額 = 小計 - 折扣」的算術不變式 |
| `checkout_error` | 結帳頁面出現 JavaScript 錯誤或 500 | Critical | ReliabilityBench: 需區分「環境故障」與「站點故障」 |
| `payment_gateway_timeout` | 支付頁面載入超過 30s | Critical | HxAgent: 超時應視為獨立故障類別 |
| `product_unavailable` | 測試 SKU 顯示缺貨或不存在 | Warning | WebTestPilot: 需驗證商品狀態符號 |
| `price_mismatch` | 結帳價格與商品頁價格不一致 | Critical | WebTestPilot: 跨狀態價格一致性檢查 |
| `ui_regression` | 重要元素消失或樣式異常 | Warning | Agent A/B: UI 變化可能影響轉換率 |
| `shipping_error` | 運送資訊無法提交 | Warning | 2506.02529: 動態表單欄位可能未完全探索 |
| `login_required` | 未登入無法完成結帳（新發現類型）| Info | Day 1 測試發現：需標示為「預期限制」而非故障 |
| `captcha_blocked` | 被驗證碼阻擋 | Info | Open CaptchaWorld: CAPTCHA 應報告為阻擋，非求解 |
| `bot_detection` | 被 WAF/Cloudflare 攔截 | Info | 多層指紋辨識研究: 需與商家約定 IP 白名單 |

### 符號化斷言檢查（來自 WebTestPilot）

**📚 論文來源**: WebTestPilot (2602.11724) 提出將網頁提取為「符號」（如 Cart、Product、Discount），並用程式碼式斷言檢查不變式。

CartRescue 應在每次巡檢中提取以下符號並檢查算術關係：

```python
# 符號化斷言檢查（參考 WebTestPilot 方法論）
def check_checkout_invariants(state):
    """
    檢查結帳流程的算術不變式
    """
    assertions = []
    
    # 1. 折扣計算正確性
    if state.discount_code_applied:
        expected_total = state.subtotal - state.discount_amount
        assertions.append(
            state.total == expected_total,
            f"折扣計算錯誤: {state.subtotal} - {state.discount_amount} ≠ {state.total}"
        )
    
    # 2. 稅額計算正確性（如適用）
    if state.tax_amount:
        expected_total = state.subtotal - state.discount_amount + state.tax_amount
        assertions.append(
            abs(state.total - expected_total) < 0.01,
            f"總額計算錯誤: 預期 {expected_total}, 實際 {state.total}"
        )
    
    # 3. 商品數量一致性（跨頁面比對）
    assertions.append(
        state.cart_item_count == state.checkout_item_count,
        f"商品數量不一致: 購物車 {state.cart_item_count}, 結帳頁 {state.checkout_item_count}"
    )
    
    return assertions
```

### 信心分數算法（增強版）

> **📚 論文佐證**: 結合 AgentRewardBench (2504.08942) 的「判斷精確度」與 HxAgent (2608.15491) 的「每步主動修正」機制。

```python
def calculate_confidence_score(
    step_results: list[StepResult],
    llm_judgment: LLMOutput,
    historical_baseline: Baseline,
    symbol_assertions: list[Assertion]  # 新增：符號化斷言結果
) -> int:
    """
    綜合計算信心分數 (0-100)，整合論文最佳實踐
    """
    scores = []
    
    # 1. 步驟成功率 (0-30 分) [原 40 → 調降，騰出空間給斷言]
    success_rate = sum(1 for s in step_results if s.success) / len(step_results)
    scores.append(success_rate * 30)
    
    # 2. 符號化斷言通過率 (0-25 分) [新增，來自 WebTestPilot]
    if symbol_assertions:
        assertion_rate = sum(1 for a in symbol_assertions if a.passed) / len(symbol_assertions)
        scores.append(assertion_rate * 25)
    else:
        scores.append(0)
    
    # 3. LLM 判斷分數 (0-25 分) [原 35 → 調降]
    llm_score = llm_judgment.confidence * 25
    scores.append(llm_score)
    
    # 4. 歷史一致性 (0-10 分) [原 15 → 調降]
    if historical_baseline:
        similarity = compare_with_baseline(step_results, historical_baseline)
        scores.append(similarity * 10)
    else:
        scores.append(10)
    
    # 5. 效能指標 (0-10 分)
    avg_load_time = mean(s.load_time for s in step_results)
    if avg_load_time < 3: scores.append(10)
    elif avg_load_time < 5: scores.append(7)
    elif avg_load_time < 10: scores.append(4)
    else: scores.append(0)
    
    return min(100, int(sum(scores)))
```

---

## 安全與合規規格

### 1. 支付安全
- **絕不完成付款**：Stagehand 在支付頁面停止，不輸入真實信用卡，不點擊「Pay Now」
- **測試 SKU**：使用專用測試商品（價格 $0.01，庫存鎖定為測試用）
- **測試環境偵測**：若偵測到 `?cartrescue=test` 參數，商店後台可自動識別為測試訂單

### 2. IP 與代理管理
- **IP 白名單**：用戶可設定允許的 IP 範圍
- **代理輪替**：使用 Bright Data / Oxylabs 住宅代理，模擬真實用戶 IP
- **Rate Limiting**：每個網站最多每 5 分鐘巡檢一次，避免被封鎖
- **User-Agent**：使用真實瀏覽器 User-Agent，不標記為機器人

### 3. 資料隱私
- **GDPR 合規**：
  - 不收集真實用戶資料
  - 測試訂單使用假名/假地址
  - 截圖中若出現 PII，自動模糊處理
- **資料保留**：
  - 截圖保留 30 天，之後自動刪除
  - 異常記錄保留 1 年
  - 用戶可隨時導出或刪除自己的資料

### 4. 帳號安全
- **JWT + Refresh Token**：Supabase Auth 標準實作
- **2FA**：支援 TOTP（Phase 2）
- **API Key 輪替**：支援生成與撤銷
- **Webhook 簽名**：n8n webhook 使用 HMAC-SHA256 簽名驗證

### 5. 合規認證目標
- **SOC 2 Type II**：12 個月內取得（Phase 2）
- **ISO 27001**：18 個月內取得（Phase 3）

---

## 效能目標

### 巡檢時間
| 指標 | 目標 | 說明 |
|------|------|------|
| 單次完整巡檢 | < 5 分鐘 | 6 步驟購物流程 |
| 單步驟執行 | < 30 秒 | 含截圖與 DOM 擷取 |
| LLM 判斷 | < 30 秒 | 含圖片上傳與推理 |
| 總端到端時間 | < 5 分鐘 | 從觸發到結果回傳 |

### 警報延遲
| 指標 | 目標 | 說明 |
|------|------|------|
| 異常發現到警報 | < 1 分鐘 | 信心分數低於閾值後 |
| 警報到通知送達 | < 30 秒 | Slack / Email / Webhook |
| n8n 觸發到執行 | < 10 秒 | Webhook 到 workflow 開始 |

### 併發與規模
| 指標 | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|
| 同時巡檢數 | 10 | 100 | 500 |
| 每日巡檢次數 | 1,000 | 10,000 | 50,000 |
| 支援網站數 | 100 | 1,000 | 5,000 |
| API RPS | 50 | 500 | 2,000 |
| 資料儲存 | 100GB/月 | 1TB/月 | 5TB/月 |

### 可用性
- **SLA 目標**：99.5%（Phase 1）→ 99.9%（Phase 2）
- **備份策略**：每日自動備份 Supabase，截圖儲存於 R2（11 個 9 耐用性）
- **災難恢復**：RTO < 4 小時，RPO < 1 小時

---

## 風險與假設

### 高風險
| 風險 | 影響 | 對策 | 論文佐證 |
|------|------|------|---------|
| 電商平台阻擋爬蟲 | 無法巡檢 | 使用住宅代理、模擬真實行為、與平台溝通 | 2606.30119: 多層指紋辨識達 0.993 準確率，無法隱藏，需允許清單 |
| LLM 判斷不準 | 誤報/漏報 | 多模型投票、持續調教 prompt、人工回饋迴路 | AgentRewardBench: 自動評估判斷精確度僅 75-85%，需人類驗證 |
| n8n 修復誤操作 | 資料損壞 | 僅執行只讀或安全操作、修復前人工確認（Phase 1）| ST-WebAgentBench: 需政策層級控制 |

### 中風險
| 風險 | 影響 | 對策 |
|------|------|------|
| 競品快速跟進 | 差異化縮小 | 持續迭代、建立社群護城河 |
| 定價壓力 | 利潤壓縮 | 價值定價、展示 ROI |
| 技術債務 | 維護困難 | 嚴格 Code Review、自動化測試 |

### 核心假設
1. 電商願意為「預防收入損失」付費（相較於「分析已發生的問題」）
2. LLM 視覺理解能力持續提升且成本下降
3. Stagehand + Playwright 組合足以應對主流電商平台
4. n8n 生態持續成熟，自動化整合成本可控

---

## 文獻研究與技術決策

### 46 篇 arXiv 論文對 CartRescue AI 的關鍵啟發

> **📚 研究基礎**: 以下技術決策均基於 46 篇 arXiv 論文的系統性文獻回顧（systematic review），涵蓋 Web Agent、GUI 自動化、電子商務測試、安全性與可靠性等領域。

#### 1. 符號化斷言檢查（來自 WebTestPilot, 2602.11724）

**核心發現**: WebTestPilot 提出將網頁提取為「符號」（如 Cart、Product、Discount），並用程式碼式斷言檢查不變式，達到 0.96 精度與 0.96 召回率。

**CartRescue 應用**: 
- 提取購物車、商品、折扣等「符號」
- 檢查算術不變式（如「總額 = 小計 - 折扣 + 稅額」）
- 跨狀態一致性檢查（商品頁價格 vs 結帳頁價格）

#### 2. 每步主動修正（來自 HxAgent, 2608.15491）

**核心發現**: HxAgent 在每一步後都執行「狀態評估器」，決定「完成/停止/繼續」，而非等整個流程跑完才檢查。在 MiniWoB++ 達到 97.4% Exact-Match。

**CartRescue 應用**:
- 每步結帳後檢查是否偏離預期
- 即時發現「加入購物車」失敗，而非等到最後
- 降低整體故障恢復時間

#### 3. 工作流記憶與快取（來自 AWM & APC, 2409.07429 & 2506.14852）

**核心發現**: Agent Workflow Memory 自動將成功執行轉為可重複子程序；Agentic Plan Caching 快取成功計畫範本，降低 40-60% LLM 成本。

**CartRescue 應用**:
- 為每個商家自動建立專屬結帳工作流
- 成功流程快取，LLM 只在重播失敗時才被呼叫
- 大幅降低 Enterprise 方案的運算成本

#### 4. Accessibility Tree 優先（來自 WebMall, 2508.13024）

**核心發現**: 在結帳任務上，Accessibility Tree 代理達到 100% 成功率，而純截圖代理會崩潰。

**CartRescue 應用**:
- 以 Accessibility Tree 為主要輸入（6,000 tokens 覆蓋 90% 觀察）
- 截圖作為輔助（處理視覺異常如 canvas、CSS 繪製的錯誤訊息）
- 雙軌輸入確保穩定性

#### 5. 安全性防禦（來自 WASP, EIA, WebInject, AdvAgent）

**核心發現**: 
- WASP (2504.18575): 網站上的使用者生成內容是提示注入攻擊面
- EIA (2409.11295): 環境注入攻擊可導致隱私洩漏
- WebInject (2505.11717): 像素級變更可誤導截圖代理
- AdvAgent (2410.17401): 惡意網站可讓代理輸入錯誤值

**CartRescue 應用**:
- 輸入折扣碼時驗證實際輸入值（非僅依賴頁面文字）
- 點擊座標與 DOM 元素交叉驗證
- 政策層級控制：組織規則 > 用戶偏好 > 任務指令
- 絕不完成付款（Destructive Action 硬阻擋）

#### 6. 自我修復定位器（來自 Self-Healing Locator, 2603.20358）

**核心發現**: 使用 Accessibility Tree 的十層定位器策略（role+name → data-testid → id → ARIA label → ...），快取成功選擇器，失敗時僅重新提取該元素，達到 $0 API 成本。

**CartRescue 應用**:
- 第一層：零成本規則定位（Accessibility Tree）
- 第二層：LLM 視覺定位（僅在第一層失敗時）
- 自我修復：商家網站微調時自動適應

---

## 附錄：文獻索引

| 論文 ID | 標題 | 對 CartRescue 的貢獻 |
|---------|------|---------------------|
| 2602.11724 | WebTestPilot: Agentic End-to-End Web Testing | 符號化斷言檢查方法論 |
| 2608.15491 | HxAgent: Iterative Agent Planning | 每步主動修正機制 |
| 2409.07429 | Agent Workflow Memory | 自動工作流記憶 |
| 2506.14852 | Agentic Plan Caching | 計畫快取降成本 |
| 2508.13024 | WebMall: Multi-Shop Benchmark | Accessibility Tree 優先策略 |
| 2603.20358 | Zero-Cost Self-Healing Test Automation | 自我修復定位器 |
| 2504.18575 | WASP: Web Agent Security Benchmark | 安全性防禦設計 |
| 2409.11295 | EIA: Environmental Injection Attack | 輸入驗證重要性 |
| 2505.11717 | WebInject: Prompt Injection Attack | 視覺驗證弱點 |
| 2410.17401 | AdvAgent: Blackbox Red-teaming | 對抗性測試 |
| ... | ... | ... |

*完整 46 篇論文摘要見 `summaries.md`，157 個技術術詞彙表見 `glossary.md`。*

---

*文件由 CartRescue AI Scout AI 引擎自動生成。已整合 46 篇 arXiv 論文研究成果。*
