#!/usr/bin/env python3
"""
CartRescue AI — Alert Service 整合測試
用途：驗證異常寫入 Supabase 與 Critical 異常 LINE 推播

執行方式:
    python tests/test_alert_service.py

環境變數（可選，若未設定則使用 Mock 模式）:
    SUPABASE_URL, SUPABASE_KEY
    LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID

測試項目:
    1. 單次異常寫入 Supabase（Mock 或真實）
    2. Critical 異常觸發 LINE 推播（10 秒內送達）
    3. Warning 異常彙整推播
"""

import os
import sys
import time
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

# 將 src/ 加入模組搜尋路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from alert_service import AlertService, save_and_alert, SEVERITY_CRITICAL, SEVERITY_WARNING, SEVERITY_INFO


# ═══════════════════════════════════════════════════════
# Mock 異常資料（與 rule_engine.py 輸出格式一致）
# ═══════════════════════════════════════════════════════

MOCK_CRITICAL_ANOMALY = {
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
        "performance": {"load_time": 2.5, "http_status": 200},
        "errors": {"js_errors": [], "console_errors": []},
        "page_text_snippet": "",
    },
}

MOCK_WARNING_ANOMALY = {
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

MOCK_INFO_ANOMALY = {
    "anomaly_detected": True,
    "type": "login_required",
    "severity": "info",
    "confidence": 100,
    "description": "該網站需登入會員才能進入結帳流程，這是預期行為",
    "suggested_fix": "若需測試完整結帳，請提供測試帳號或調整審計範圍",
    "rule_id": "RULE-008",
    "detected_at": datetime.now(timezone.utc).isoformat(),
    "evidence": {"url": "https://example.com/login"},
}


# ═══════════════════════════════════════════════════════
# 測試類別
# ═══════════════════════════════════════════════════════

class TestAlertServiceUnit(unittest.TestCase):
    """AlertService 單元測試（Mock，不依賴外部服務）"""

    def test_should_alert_critical(self):
        """Critical 異常應回傳 True"""
        self.assertTrue(AlertService.should_alert(SEVERITY_CRITICAL))

    def test_should_alert_warning(self):
        """Warning 異常應回傳 True"""
        self.assertTrue(AlertService.should_alert(SEVERITY_WARNING))

    def test_should_alert_info(self):
        """Info 異常應回傳 False"""
        self.assertFalse(AlertService.should_alert(SEVERITY_INFO))

    def test_save_anomaly_without_supabase(self):
        """未設定 Supabase 時應 graceful 降級"""
        svc = AlertService(supabase_url="", supabase_key="")
        result = svc.save_anomaly(MOCK_CRITICAL_ANOMALY)
        self.assertFalse(result["success"])
        self.assertIsNotNone(result["error"])

    def test_send_line_alert_without_token(self):
        """未設定 LINE token 時應 graceful 降級"""
        svc = AlertService(line_token="", line_user_id="")
        result = svc.send_line_alert(MOCK_CRITICAL_ANOMALY)
        self.assertFalse(result["success"])
        self.assertIn("待填入", result["error"])

    def test_send_batch_line_alert_empty(self):
        """空列表批次推播應直接回傳成功"""
        svc = AlertService()
        result = svc.send_batch_line_alert([])
        self.assertTrue(result["success"])

    def test_send_batch_line_alert_without_token(self):
        """未設定 LINE token 時批次推播應 graceful 降級"""
        svc = AlertService(line_token="", line_user_id="")
        result = svc.send_batch_line_alert([MOCK_WARNING_ANOMALY])
        self.assertFalse(result["success"])
        self.assertIn("待填入", result["error"])

    @patch("alert_service.requests.post")
    def test_send_line_alert_success(self, mock_post):
        """模擬 LINE API 成功回應"""
        mock_post.return_value = Mock(
            status_code=200,
            headers={"X-Request-Id": "test-msg-id-123"},
            raise_for_status=Mock(),
        )
        svc = AlertService(
            line_token="TEST_TOKEN",
            line_user_id="TEST_USER_ID",
        )
        result = svc.send_line_alert(MOCK_CRITICAL_ANOMALY)
        self.assertTrue(result["success"])
        self.assertEqual(result["message_id"], "test-msg-id-123")
        mock_post.assert_called_once()

    @patch("alert_service.requests.post")
    def test_send_line_alert_timeout(self, mock_post):
        """模擬 LINE API 超時"""
        import requests as req
        mock_post.side_effect = req.exceptions.Timeout("Connection timed out")
        svc = AlertService(
            line_token="TEST_TOKEN",
            line_user_id="TEST_USER_ID",
        )
        result = svc.send_line_alert(MOCK_CRITICAL_ANOMALY)
        self.assertFalse(result["success"])
        self.assertIn("超時", result["error"])

    @patch("alert_service.requests.post")
    def test_send_line_alert_under_10_seconds(self, mock_post):
        """驗證 LINE 推播在 10 秒內完成（模擬）"""
        mock_post.return_value = Mock(
            status_code=200,
            headers={"X-Request-Id": "test-msg-id-456"},
            raise_for_status=Mock(),
        )
        svc = AlertService(
            line_token="TEST_TOKEN",
            line_user_id="TEST_USER_ID",
        )
        start = time.time()
        result = svc.send_line_alert(MOCK_CRITICAL_ANOMALY)
        elapsed = time.time() - start
        self.assertTrue(result["success"])
        self.assertLess(elapsed, 10.0, f"推播耗時 {elapsed:.2f} 秒，超過 10 秒限制")

    @patch("alert_service.create_client")
    def test_save_anomaly_success(self, mock_create_client):
        """模擬 Supabase 寫入成功"""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": "mock-uuid-123"}]
        mock_table.insert.return_value.execute.return_value = mock_response
        mock_client.table.return_value = mock_table
        mock_create_client.return_value = mock_client

        svc = AlertService(
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
        )
        result = svc.save_anomaly(MOCK_CRITICAL_ANOMALY)
        self.assertTrue(result["success"])
        self.assertEqual(result["id"], "mock-uuid-123")

    def test_save_and_alert_convenience(self):
        """save_and_alert 便利函式應正確組合儲存與推播"""
        # 未設定任何 key，應回傳兩者皆失敗
        result = save_and_alert(MOCK_CRITICAL_ANOMALY)
        self.assertFalse(result["saved"]["success"])
        # 錯誤訊息可能是「未初始化」或「待填入」
        self.assertTrue(
            "未初始化" in result["saved"]["error"] or "待填入" in result["saved"]["error"],
            f"Unexpected error message: {result['saved']['error']}",
        )


class TestAlertServiceIntegration(unittest.TestCase):
    """
    AlertService 整合測試（需設定真實 API key）
    若環境變數未設定，測試自動跳過。
    """

    @classmethod
    def setUpClass(cls):
        cls.has_supabase = bool(
            os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY")
        )
        cls.has_line = bool(
            os.getenv("LINE_CHANNEL_ACCESS_TOKEN") and os.getenv("LINE_USER_ID")
        )

    @unittest.skipUnless(
        bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY")),
        "未設定 SUPABASE_URL / SUPABASE_KEY，跳過真實 Supabase 測試",
    )
    def test_real_supabase_insert(self):
        """真實 Supabase 單筆寫入測試"""
        svc = AlertService()
        result = svc.save_anomaly(MOCK_CRITICAL_ANOMALY)
        self.assertTrue(
            result["success"],
            f"Supabase 寫入失敗：{result.get('error')}",
        )
        self.assertIsNotNone(result["id"])
        print(f"\n  ✅ 真實 Supabase 寫入成功，id={result['id']}")

    @unittest.skipUnless(
        bool(os.getenv("LINE_CHANNEL_ACCESS_TOKEN") and os.getenv("LINE_USER_ID")),
        "未設定 LINE_CHANNEL_ACCESS_TOKEN / LINE_USER_ID，跳過真實 LINE 測試",
    )
    def test_real_line_push_critical(self):
        """真實 LINE Critical 推播測試（10 秒內送達）"""
        svc = AlertService()
        start = time.time()
        result = svc.send_line_alert(MOCK_CRITICAL_ANOMALY)
        elapsed = time.time() - start
        self.assertTrue(
            result["success"],
            f"LINE 推播失敗：{result.get('error')}",
        )
        self.assertLess(elapsed, 10.0, f"推播耗時 {elapsed:.2f} 秒，超過 10 秒限制")
        print(f"\n  ✅ 真實 LINE 推播成功，耗時 {elapsed:.2f} 秒")


# ═══════════════════════════════════════════════════════
# 主程式
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("CartRescue Alert Service 測試")
    print("=" * 60)

    # 顯示環境變數狀態
    env_status = {
        "SUPABASE_URL": bool(os.getenv("SUPABASE_URL")),
        "SUPABASE_KEY": bool(os.getenv("SUPABASE_KEY")),
        "LINE_CHANNEL_ACCESS_TOKEN": bool(os.getenv("LINE_CHANNEL_ACCESS_TOKEN")),
        "LINE_USER_ID": bool(os.getenv("LINE_USER_ID")),
    }
    print("\n環境變數狀態：")
    for k, v in env_status.items():
        print(f"  {'✅' if v else '❌'} {k}")

    print("\n" + "=" * 60)
    print("執行測試...")
    print("=" * 60 + "\n")

    unittest.main(verbosity=2)
