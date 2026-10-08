#!/usr/bin/env python3
"""
CartRescue AI — 警報服務（Alert Service v1）
用途：異常結果儲存至 Supabase，並依嚴重度觸發 LINE 推播

設計哲學：
- save_anomaly(): 每筆異常立即寫入資料庫，確保審計軌跡完整
- send_line_alert(): Critical 異常即時推播，Warning 異常彙整推播
- should_alert(): 統一判斷邏輯，避免重複推播

依賴：
- supabase-py（Supabase 官方 Python 客戶端）
- requests（LINE Messaging API HTTP 呼叫）

環境變數：
- SUPABASE_URL: Supabase 專案 URL
- SUPABASE_KEY: Supabase Service Role Key（具寫入權限）
- LINE_CHANNEL_ACCESS_TOKEN: LINE Messaging API Channel Access Token
- LINE_USER_ID: 推播對象的 LINE User ID（或 Group ID）
"""

import os
import json
import time
from typing import Dict, Optional, Any
from datetime import datetime, timezone
from dataclasses import asdict

import requests

# 嘗試匯入 Supabase 客戶端，未安裝時設為 None（便於測試 patch）
try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None


# ═══════════════════════════════════════════════════════
# 常數與設定
# ═══════════════════════════════════════════════════════

SEVERITY_CRITICAL = "critical"
SEVERITY_WARNING = "warning"
SEVERITY_INFO = "info"

LINE_API_URL = "https://api.line.me/v2/bot/message/push"
LINE_API_TIMEOUT = 10  # 秒，確保 10 秒內送達

SUPABASE_TABLE = "anomalies"


# ═══════════════════════════════════════════════════════
# AlertService 主類別
# ═══════════════════════════════════════════════════════

class AlertService:
    """
    CartRescue AI 警報服務

    用法:
        from alert_service import AlertService
        svc = AlertService()
        svc.save_anomaly(anomaly_dict)
        if svc.should_alert(anomaly_dict["severity"]):
            svc.send_line_alert(anomaly_dict)
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        line_token: Optional[str] = None,
        line_user_id: Optional[str] = None,
    ):
        """
        初始化 AlertService。
        參數優先順序：顯式傳入 > 環境變數 > None（待填入）
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL", "")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY", "")
        self.line_token = line_token or os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
        self.line_user_id = line_user_id or os.getenv("LINE_USER_ID", "")

        # 嘗試初始化 Supabase 客戶端（若已安裝 supabase-py）
        self._supabase = self._init_supabase()

    def _init_supabase(self):
        """初始化 Supabase 客戶端，未安裝或缺少設定時回傳 None"""
        if create_client is not None and self.supabase_url and self.supabase_key:
            return create_client(self.supabase_url, self.supabase_key)
        return None

    # ── 公開方法 ─────────────────────────────

    def save_anomaly(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """
        將單筆異常結果寫入 Supabase `anomalies` 資料表。

        參數:
            anomaly: 異常字典（需與 rule_engine.py 的 AnomalyResult 格式一致）

        回傳:
            {"success": bool, "id": str|None, "error": str|None}
        """
        if not self._supabase:
            return {
                "success": False,
                "id": None,
                "error": (
                    "Supabase 客戶端未初始化。"
                    "請確認已安裝 supabase-py 並設定 SUPABASE_URL / SUPABASE_KEY。"
                ),
            }

        # 補上寫入時間戳
        payload = dict(anomaly)
        payload.setdefault("created_at", datetime.now(timezone.utc).isoformat())

        # evidence 與其他 dict/list 欄位需序列化為 JSON（若資料表使用 jsonb）
        payload = self._serialize_complex_fields(payload)

        try:
            response = self._supabase.table(SUPABASE_TABLE).insert(payload).execute()
            # supabase-py v2 回傳結構：response.data[0]
            data = response.data if response.data else []
            inserted = data[0] if data else {}
            return {
                "success": True,
                "id": inserted.get("id"),
                "error": None,
            }
        except Exception as e:
            return {
                "success": False,
                "id": None,
                "error": str(e),
            }

    def send_line_alert(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """
        透過 LINE Messaging API 發送推播訊息。
        Critical 異常立即推播；Warning 彙整後推播（由呼叫方控制）。

        參數:
            anomaly: 異常字典

        回傳:
            {"success": bool, "message_id": str|None, "error": str|None}
        """
        if not self.line_token:
            return {
                "success": False,
                "message_id": None,
                "error": "LINE_CHANNEL_ACCESS_TOKEN 未設定（待填入 API key）",
            }

        if not self.line_user_id:
            return {
                "success": False,
                "message_id": None,
                "error": "LINE_USER_ID 未設定（待填入推播對象 ID）",
            }

        # 組裝推播訊息
        severity_emoji = {
            SEVERITY_CRITICAL: "🔴",
            SEVERITY_WARNING: "🟡",
            SEVERITY_INFO: "🔵",
        }.get(anomaly.get("severity", ""), "⚪")

        text = (
            f"{severity_emoji} CartRescue AI 異常警報\n"
            f"類型：{anomaly.get('type', 'N/A')}\n"
            f"嚴重度：{anomaly.get('severity', 'N/A').upper()}\n"
            f"信心度：{anomaly.get('confidence', 'N/A')}%\n"
            f"說明：{anomaly.get('description', 'N/A')}\n"
            f"建議：{anomaly.get('suggested_fix', 'N/A')}\n"
            f"規則：{anomaly.get('rule_id', 'N/A')}\n"
            f"時間：{anomaly.get('detected_at', datetime.now(timezone.utc).isoformat())}"
        )

        headers = {
            "Authorization": f"Bearer {self.line_token}",
            "Content-Type": "application/json",
        }
        body = {
            "to": self.line_user_id,
            "messages": [
                {
                    "type": "text",
                    "text": text,
                }
            ],
        }

        try:
            resp = requests.post(
                LINE_API_URL,
                headers=headers,
                json=body,
                timeout=LINE_API_TIMEOUT,
            )
            resp.raise_for_status()
            return {
                "success": True,
                "message_id": resp.headers.get("X-Request-Id"),
                "error": None,
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message_id": None,
                "error": f"LINE API 請求超時（>{LINE_API_TIMEOUT}秒）",
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message_id": None,
                "error": f"LINE API 請求失敗：{e}",
            }

    @staticmethod
    def should_alert(severity: str) -> bool:
        """
        判斷該嚴重度是否需要推播。

        策略：
        - Critical → 立即推播（True）
        - Warning  → 彙整推播（True，但建議由呼叫方累積後批次發送）
        - Info     → 不推播（False）
        """
        return severity.lower() in (SEVERITY_CRITICAL, SEVERITY_WARNING)

    # ── 批次彙整推播（Warning 級別建議使用）────────────────

    def send_batch_line_alert(self, anomalies: list) -> Dict[str, Any]:
        """
        將多筆 Warning 異常彙整為一則 LINE 推播，避免訊息轟炸。

        參數:
            anomalies: 異常字典列表

        回傳:
            {"success": bool, "message_id": str|None, "error": str|None}
        """
        if not anomalies:
            return {"success": True, "message_id": None, "error": None}

        if not self.line_token or not self.line_user_id:
            return {
                "success": False,
                "message_id": None,
                "error": "LINE_CHANNEL_ACCESS_TOKEN 或 LINE_USER_ID 未設定（待填入 API key）",
            }

        lines = ["🟡 CartRescue AI — Warning 異常彙整"]
        for idx, a in enumerate(anomalies[:10], 1):
            lines.append(
                f"\n{idx}. {a.get('type', 'N/A')} "
                f"（信心度 {a.get('confidence', 'N/A')}%）\n"
                f"   說明：{a.get('description', 'N/A')}"
            )
        if len(anomalies) > 10:
            lines.append(f"\n... 尚有 {len(anomalies) - 10} 筆異常未列出")

        text = "\n".join(lines)

        headers = {
            "Authorization": f"Bearer {self.line_token}",
            "Content-Type": "application/json",
        }
        body = {
            "to": self.line_user_id,
            "messages": [{"type": "text", "text": text}],
        }

        try:
            resp = requests.post(
                LINE_API_URL,
                headers=headers,
                json=body,
                timeout=LINE_API_TIMEOUT,
            )
            resp.raise_for_status()
            return {
                "success": True,
                "message_id": resp.headers.get("X-Request-Id"),
                "error": None,
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message_id": None,
                "error": f"LINE API 請求超時（>{LINE_API_TIMEOUT}秒）",
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message_id": None,
                "error": f"LINE API 請求失敗：{e}",
            }

    # ── 內部工具方法 ──────────────────────────

    @staticmethod
    def _serialize_complex_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        將 dict / list 欄位序列化為 JSON 字串，
        確保與 PostgreSQL jsonb 欄位相容。
        """
        result = {}
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                result[key] = json.dumps(value, ensure_ascii=False, default=str)
            else:
                result[key] = value
        return result


# ═══════════════════════════════════════════════════════
# 便利函式（函式式介面）
# ═══════════════════════════════════════════════════════

def save_and_alert(anomaly: Dict[str, Any]) -> Dict[str, Any]:
    """
    一鍵儲存 + 判斷推播的便利函式。

    回傳:
        {
            "saved": {...},
            "alerted": {...},
        }
    """
    svc = AlertService()
    saved = svc.save_anomaly(anomaly)
    alerted = {"success": True, "message_id": None, "error": "未觸發推播"}

    if svc.should_alert(anomaly.get("severity", "")):
        alerted = svc.send_line_alert(anomaly)

    return {"saved": saved, "alerted": alerted}


# ═══════════════════════════════════════════════════════
# 單元測試（獨立執行時）
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("AlertService 單元測試（使用 Mock）")
    print("=" * 60)

    # Mock 異常資料（與 rule_engine.py 輸出一致）
    sample_critical = {
        "anomaly_detected": True,
        "type": "discount_calculation_error",
        "severity": "critical",
        "confidence": 100,
        "description": "折扣計算錯誤：小計 NT$3580 - 折扣 NT$500 + 稅額 NT$0 ≠ 總額 NT$3200",
        "suggested_fix": "檢查結帳頁面的折扣計算邏輯，確認前端/後端計算公式一致",
        "rule_id": "RULE-001",
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "evidence": {
            "url": "https://example.com/checkout",
            "prices": {"subtotal": 3580, "discount": 500, "total": 3200, "tax": 0},
        },
    }

    sample_warning = {
        "anomaly_detected": True,
        "type": "element_missing",
        "severity": "warning",
        "confidence": 90,
        "description": "結帳頁關鍵元素消失：checkout-button, payment-form",
        "suggested_fix": "檢查前台上版紀錄，確認相關元素未被誤刪或 CSS 隱藏",
        "rule_id": "RULE-006",
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "evidence": {
            "url": "https://example.com/checkout",
            "elements_missing": ["checkout-button", "payment-form"],
        },
    }

    # 測試 1: should_alert
    svc = AlertService()
    assert svc.should_alert("critical") is True
    assert svc.should_alert("warning") is True
    assert svc.should_alert("info") is False
    print("\n[測試 1] should_alert()")
    print("  ✅ Critical / Warning 回傳 True，Info 回傳 False")

    # 測試 2: 未設定 API key 時 graceful 降級
    print("\n[測試 2] save_anomaly()（未設定 Supabase）")
    result = svc.save_anomaly(sample_critical)
    assert result["success"] is False
    assert "待填入" in result["error"] or "未初始化" in result["error"]
    print(f"  ✅ 未設定時回傳錯誤提示：{result['error'][:40]}...")

    print("\n[測試 3] send_line_alert()（未設定 LINE）")
    result = svc.send_line_alert(sample_critical)
    assert result["success"] is False
    assert "待填入" in result["error"] or "未設定" in result["error"]
    print(f"  ✅ 未設定時回傳錯誤提示：{result['error'][:40]}...")

    # 測試 4: 批次推播空列表
    print("\n[測試 4] send_batch_line_alert([])")
    result = svc.send_batch_line_alert([])
    assert result["success"] is True
    print("  ✅ 空列表直接回傳成功")

    # 測試 5: 批次推播未設定 LINE
    print("\n[測試 5] send_batch_line_alert()（未設定 LINE）")
    result = svc.send_batch_line_alert([sample_warning])
    assert result["success"] is False
    print(f"  ✅ 未設定時回傳錯誤提示：{result['error'][:40]}...")

    print(f"\n{'=' * 60}")
    print("AlertService 單元測試全部通過 ✅")
    print(f"{'=' * 60}")
