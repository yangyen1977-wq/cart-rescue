# CartRescue AI — 異常儲存與 LINE 推播整合指南

> 版本：v1.0  
> 用途：引導團隊完成 Supabase 資料表建立與 LINE Messaging API 串接

---

## 一、架構總覽

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  rule_engine.py │────>│ alert_service.py │────>│  Supabase   │
│  （異常檢測）    │     │  （儲存 + 推播）  │     │ （PostgreSQL）│
└─────────────────┘     └──────────────────┘     └─────────────┘
                                  │
                                  ▼
                          ┌─────────────┐
                          │  LINE API   │
                          │ （即時推播） │
                          └─────────────┘
```

| 元件 | 職責 |
|------|------|
| `rule_engine.py` | 產生異常結果（`AnomalyResult`） |
| `alert_service.py` | `save_anomaly()` 寫入資料庫、`send_line_alert()` 發送推播 |
| `supabase_schema.sql` | PostgreSQL 建表腳本與索引 |
| `test_alert_service.py` | 單元測試（Mock）與整合測試（真實 API） |

---

## 二、環境變數設定

在專案根目錄建立 `.env` 檔案（**切勿提交至 Git**）：

```bash
# ── Supabase ──
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_KEY=<service_role_key>

# ── LINE Messaging API ──
LINE_CHANNEL_ACCESS_TOKEN=<channel_access_token>
LINE_USER_ID=<target_user_id>
```

### 2.1 Supabase 憑證取得方式

1. 前往 [Supabase Dashboard](https://app.supabase.com/)
2. 進入專案 → **Project Settings** → **API**
3. 複製 **URL** 與 **service_role key**（`eyJhbG...`，非 `anon` key）

### 2.2 LINE Messaging API 憑證取得方式

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 建立 Provider → 建立 Messaging API Channel
3. 進入 Channel → **Messaging API** → 複製 **Channel Access Token**（長期）
4. 取得推播對象的 `LINE_USER_ID`：
   - 使用 [webhook 接收 follow 事件](https://developers.line.biz/en/reference/messaging-api/#follow-event)
   - 或使用 [LINE Notify](https://notify-bot.line.me/) 作為簡易替代方案（見附錄）

---

## 三、資料表建立

在 Supabase SQL Editor 中貼上並執行 [`docs/supabase_schema.sql`](./supabase_schema.sql)，將建立：

| 物件 | 說明 |
|------|------|
| `anomalies` | 主資料表，欄位與 `AnomalyResult` 一一對應 |
| 索引 | `severity`、`type`、`detected_at`、`alerted` 等加速查詢 |
| RLS 策略 | `service_role` 具完整權限，後端寫入用 |
| 視圖 `warning_summary_last_hour` | 每小時 Warning 統計彙整 |
| 觸發器 `trg_anomalies_alert_sent` | 自動記錄 `alert_sent_at` 時間戳 |

### 3.1 資料表結構對應

| `rule_engine.py` 欄位 | `anomalies` 欄位 | PostgreSQL 型別 |
|----------------------|------------------|----------------|
| `anomaly_detected` | `anomaly_detected` | `BOOLEAN` |
| `type` | `type` | `TEXT` |
| `severity` | `severity` | `TEXT` + `CHECK` |
| `confidence` | `confidence` | `INTEGER` (0–100) |
| `description` | `description` | `TEXT` |
| `suggested_fix` | `suggested_fix` | `TEXT` |
| `rule_id` | `rule_id` | `TEXT` |
| `detected_at` | `detected_at` | `TIMESTAMPTZ` |
| `evidence` | `evidence` | `JSONB` |
| — | `created_at` | `TIMESTAMPTZ`（自動） |
| — | `alerted` | `BOOLEAN`（推播狀態） |
| — | `alert_sent_at` | `TIMESTAMPTZ`（推播時間） |

---

## 四、程式碼使用範例

### 4.1 基礎用法（儲存 + 推播）

```python
from src.alert_service import AlertService

svc = AlertService()

# 假設 anomaly 來自 rule_engine.evaluate()
anomaly = {
    "anomaly_detected": True,
    "type": "discount_calculation_error",
    "severity": "critical",
    "confidence": 100,
    "description": "折扣計算錯誤：...",
    "suggested_fix": "檢查結帳頁面...",
    "rule_id": "RULE-001",
    "detected_at": "2026-10-08T12:00:00Z",
    "evidence": {"url": "https://example.com/checkout"},
}

# 1. 寫入資料庫
save_result = svc.save_anomaly(anomaly)
print("Saved:", save_result["id"])

# 2. 判斷是否需要推播
if svc.should_alert(anomaly["severity"]):
    alert_result = svc.send_line_alert(anomaly)
    print("Alerted:", alert_result["message_id"])
```

### 4.2 一鍵儲存推播

```python
from src.alert_service import save_and_alert

result = save_and_alert(anomaly)
print(result["saved"]["id"])
print(result["alerted"]["message_id"])
```

### 4.3 Warning 彙整推播

```python
warning_anomalies = [...]  # 收集多筆 warning
svc.send_batch_line_alert(warning_anomalies)
```

---

## 五、推播策略

| 嚴重度 | `should_alert()` | 建議行為 |
|--------|-------------------|----------|
| **Critical** | `True` | **立即推播**（單筆發送） |
| **Warning** | `True` | **彙整推播**（每小時 / 每批次一次） |
| **Info** | `False` | 不推播，僅記錄於資料庫 |

> 彙整推播可使用 `warning_summary_last_hour` 視圖輔助統計。

---

## 六、測試驗證

### 6.1 Mock 單元測試（無需 API key）

```bash
cd /home/cartrescue/CartRescue_AI
python tests/test_alert_service.py
```

預期結果：12 項通過，2 項跳過（真實 API）。

### 6.2 真實整合測試（需 API key）

設定環境變數後再次執行：

```bash
export SUPABASE_URL="https://..."
export SUPABASE_KEY="eyJhbG..."
export LINE_CHANNEL_ACCESS_TOKEN="..."
export LINE_USER_ID="..."
python tests/test_alert_service.py
```

預期結果：14 項全部通過，其中 `test_real_line_push_critical` 驗證推播在 **10 秒內** 完成。

---

## 七、常見問題

### Q1：未設定 API key 時會怎樣？
程式碼會 **graceful 降級**，回傳明確錯誤訊息（如「待填入 API key」），不會拋出未處理異常。

### Q2：可否改用 LINE Notify？
可以，它是較簡易的替代方案（見附錄 A）。但 LINE Messaging API 支援更豐富的訊息格式與互動。

### Q3：Supabase `service_role` key 會外洩嗎？
請將 `.env` 加入 `.gitignore`，並在部署環境使用 secrets manager（如 GitHub Actions Secrets、Docker Secrets）。

### Q4：如何擴展至多個推播對象？
將 `LINE_USER_ID` 改為列表，並在 `send_line_alert()` 中迴圈發送；或建立 `alert_recipients` 資料表管理對象。

---

## 八、附錄

### A. LINE Notify 替代方案（簡易版）

若不需 Messaging API 的進階功能，可使用 LINE Notify：

```python
import requests

def send_line_notify(message: str, token: str):
    resp = requests.post(
        "https://notify-api.line.me/api/notify",
        headers={"Authorization": f"Bearer {token}"},
        data={"message": message},
        timeout=10,
    )
    return resp.status_code == 200
```

### B. 相依套件安裝

```bash
pip install supabase requests
```

---

## 九、檔案清單

| 檔案 | 說明 |
|------|------|
| `src/alert_service.py` | 警報服務主程式 |
| `docs/supabase_schema.sql` | 建表腳本 |
| `tests/test_alert_service.py` | 單元 + 整合測試 |
| `docs/ALERT_INTEGRATION_GUIDE.md` | 本文件 |

---

*文件版本：v1.0 | 建立日期：2026-10-08 | 維護者：CartRescue AI Scout 子代理*
