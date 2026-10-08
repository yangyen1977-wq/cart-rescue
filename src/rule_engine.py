#!/usr/bin/env python3
"""
CartRescue AI — 輕量規則引擎（Rule Engine v1）
用途：第一層異常檢測，零 API 成本，毫秒級反應

設計哲學：
- 輸入「符號化狀態」（來自 WebTestPilot 方法論）
- 每條規則是「條件 → 異常類型 → 嚴重度 → 信心分數」
- 輸出與 LLM 相同的 JSON 格式，讓上層無縫切換

論文依據：
- WebTestPilot (2602.11724): 符號化 GUI 斷言檢查
- HxAgent (2608.15491): 每步狀態評估器
"""
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional
from enum import Enum
import json, time
import sys

# 整合價格提取模組
sys.path.insert(0, '/home/cartrescue/CartRescue_AI/src')
from price_extractor import extract_prices

class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class AnomalyType(str, Enum):
    DISCOUNT_CALCULATION_ERROR = "discount_calculation_error"
    DISCOUNT_NOT_APPLIED = "discount_not_applied"
    PAYMENT_TIMEOUT = "payment_timeout"
    CHECKOUT_PAGE_ERROR = "checkout_page_error"
    PRICE_MISMATCH = "price_mismatch"
    ELEMENT_MISSING = "element_missing"
    PRODUCT_UNAVAILABLE = "product_unavailable"
    LOGIN_REQUIRED = "login_required"
    CAPTCHA_BLOCKED = "captcha_blocked"
    BOT_DETECTED = "bot_detected"

@dataclass
class AuditState:
    """從 Playwright 提取的符號化狀態"""
    # 基本資訊
    url: str = ""
    page_title: str = ""
    step_name: str = ""  # 如 "checkout", "payment", "cart"
    
    # 價格符號
    subtotal: Optional[float] = None          # 小計
    discount_amount: Optional[float] = None   # 折扣金額
    total: Optional[float] = None             # 總額
    tax_amount: Optional[float] = None        # 稅額
    product_page_price: Optional[float] = None # 商品頁價格
    
    # 折扣碼符號
    discount_code_entered: Optional[str] = None    # 輸入的折扣碼
    discount_code_expected: Optional[str] = None  # 預期的折扣碼
    discount_error_message: Optional[str] = None   # 錯誤訊息文字
    
    # 效能符號
    page_load_time: Optional[float] = None    # 秒
    http_status: Optional[int] = None         # HTTP status
    
    # DOM 符號
    element_ids_present: List[str] = field(default_factory=list)
    element_ids_missing: List[str] = field(default_factory=list)
    page_text: str = ""                       # 頁面可見文字（截斷後）
    
    # 錯誤符號
    console_errors: List[str] = field(default_factory=list)
    js_errors: List[str] = field(default_factory=list)
    network_errors: List[Dict] = field(default_factory=list)
    
    # 阻擋符號
    captcha_detected: bool = False
    login_required_detected: bool = False
    bot_detected: bool = False
    waf_blocked: bool = False

    @classmethod
    def from_page_text(cls, page_text: str, url: str = "", step_name: str = "", **kwargs):
        """
        從頁面文字自動提取價格並建立 AuditState。
        會自動將第一個價格設為 product_page_price，最後一個設為 total。
        """
        prices = extract_prices(page_text)
        state = cls(
            url=url,
            step_name=step_name,
            page_text=page_text,
            **kwargs
        )
        if prices:
            state.product_page_price = prices[0]
            # 若有多個價格，最後一個常為總額
            if len(prices) > 1:
                state.total = prices[-1]
                state.subtotal = prices[0]
            else:
                state.total = prices[0]
                state.subtotal = prices[0]
        return state

@dataclass
class AnomalyResult:
    """異常結果 — 與 LLM 輸出相同格式"""
    anomaly_detected: bool
    type: str
    severity: str
    confidence: int           # 0-100
    description: str          # 繁體中文
    suggested_fix: str        # 繁體中文
    rule_id: str              # 哪條規則觸發
    detected_at: str = field(default_factory=lambda: time.strftime('%Y-%m-%dT%H:%M:%SZ'))
    evidence: Dict = field(default_factory=dict)

class RuleEngine:
    """
    規則引擎核心
    
    用法:
        engine = RuleEngine()
        state = AuditState(subtotal=3580, discount_amount=0, total=3580, ...)
        results = engine.evaluate(state)
    """
    
    def __init__(self):
        self.rules: List[Dict] = self._build_rules()
    
    def _build_rules(self) -> List[Dict]:
        """定義所有規則"""
        return [
            # ── 規則 1: 折扣計算錯誤 ──
            {
                "rule_id": "RULE-001",
                "type": AnomalyType.DISCOUNT_CALCULATION_ERROR,
                "severity": Severity.CRITICAL,
                "confidence": 100,
                "condition": lambda s: (
                    s.subtotal is not None and 
                    s.discount_amount is not None and 
                    s.total is not None and
                    abs((s.subtotal - s.discount_amount + (s.tax_amount or 0)) - s.total) > 0.01
                ),
                "description_template": "折扣計算錯誤：小計 NT${subtotal:.0f} - 折扣 NT${discount:.0f} + 稅額 NT${tax:.0f} ≠ 總額 NT${total:.0f}",
                "fix_template": "檢查結帳頁面的折扣計算邏輯，確認前端/後端計算公式一致",
            },
            
            # ── 規則 2: 折扣碼未生效 ──
            {
                "rule_id": "RULE-002",
                "type": AnomalyType.DISCOUNT_NOT_APPLIED,
                "severity": Severity.CRITICAL,
                "confidence": 95,
                "condition": lambda s: (
                    s.discount_code_entered is not None and
                    s.discount_code_entered != "" and
                    (s.discount_amount == 0 or s.discount_amount is None) and
                    (s.discount_error_message is not None or 
                     "不適用" in s.page_text or 
                     "無效" in s.page_text or
                     "invalid" in s.page_text.lower())
                ),
                "description_template": "折扣碼『{code}』未生效：頁面顯示錯誤訊息，折扣金額為 NT$0",
                "fix_template": "檢查折扣碼『{code}』的適用條件（到期日、最低消費、適用商品類別）",
            },
            
            # ── 規則 3: 支付頁面超時 ──
            {
                "rule_id": "RULE-003",
                "type": AnomalyType.PAYMENT_TIMEOUT,
                "severity": Severity.CRITICAL,
                "confidence": 100,
                "condition": lambda s: (
                    s.page_load_time is not None and 
                    s.page_load_time > 30.0 and
                    "payment" in s.step_name.lower()
                ),
                "description_template": "支付頁面載入超過 {load_time:.1f} 秒，顧客可能在此流失",
                "fix_template": "聯繫支付服務商（綠界/藍新/Stripe）確認 API 回應時間，或檢查網站 CDN 設定",
            },
            
            # ── 規則 4: 結帳頁面錯誤 ──
            {
                "rule_id": "RULE-004",
                "type": AnomalyType.CHECKOUT_PAGE_ERROR,
                "severity": Severity.CRITICAL,
                "confidence": 100,
                "condition": lambda s: (
                    s.http_status is not None and s.http_status >= 500
                ) or (
                    len(s.js_errors) > 0
                ) or (
                    "error" in s.page_text.lower() and "500" in s.page_text
                ),
                "description_template": "結帳頁面出現技術錯誤（HTTP {status} / JS Error），顧客無法完成購買",
                "fix_template": "檢查伺服器日誌、JavaScript 錯誤追蹤，優先修復影響結帳的錯誤",
            },
            
            # ── 規則 5: 價格不一致 ──
            {
                "rule_id": "RULE-005",
                "type": AnomalyType.PRICE_MISMATCH,
                "severity": Severity.CRITICAL,
                "confidence": 100,
                "condition": lambda s: (
                    s.product_page_price is not None and 
                    s.subtotal is not None and
                    abs(s.product_page_price - s.subtotal) > 0.01
                ),
                "description_template": "價格不一致：商品頁顯示 NT${product_price:.0f}，結帳頁顯示 NT${checkout_price:.0f}",
                "fix_template": "檢查商品頁與結帳頁的價格同步機制，確認無促銷活動或幣別轉換錯誤",
            },
            
            # ── 規則 6: 關鍵元素消失 ──
            {
                "rule_id": "RULE-006",
                "type": AnomalyType.ELEMENT_MISSING,
                "severity": Severity.WARNING,
                "confidence": 90,
                "condition": lambda s: len(s.element_ids_missing) > 0,
                "description_template": "結帳頁關鍵元素消失：{elements}，可能影響顧客完成購買",
                "fix_template": "檢查前台上版紀錄，確認相關元素未被誤刪或 CSS 隱藏",
            },
            
            # ── 規則 7: 商品缺貨 ──
            {
                "rule_id": "RULE-007",
                "type": AnomalyType.PRODUCT_UNAVAILABLE,
                "severity": Severity.WARNING,
                "confidence": 95,
                "condition": lambda s: (
                    "sold out" in s.page_text.lower() or
                    "缺貨" in s.page_text or
                    "out of stock" in s.page_text.lower() or
                    "暫無庫存" in s.page_text or
                    s.http_status == 404
                ),
                "description_template": "測試商品顯示缺貨或不存在，無法完成結帳流程審計",
                "fix_template": "確認測試 SKU 庫存狀態，或更換測試商品",
            },
            
            # ── 規則 8: 登入牆（Info 級別）──
            {
                "rule_id": "RULE-008",
                "type": AnomalyType.LOGIN_REQUIRED,
                "severity": Severity.INFO,
                "confidence": 100,
                "condition": lambda s: s.login_required_detected,
                "description_template": "該網站需登入會員才能進入結帳流程，這是預期行為",
                "fix_template": "若需測試完整結帳，請提供測試帳號或調整審計範圍",
            },
            
            # ── 規則 9: CAPTCHA 阻擋（Info 級別）──
            {
                "rule_id": "RULE-009",
                "type": AnomalyType.CAPTCHA_BLOCKED,
                "severity": Severity.INFO,
                "confidence": 100,
                "condition": lambda s: s.captcha_detected,
                "description_template": "登入頁出現驗證碼（CAPTCHA），自動化測試無法繼續",
                "fix_template": "將 CartRescue IP 加入白名單，或提供無 CAPTCHA 的測試帳號",
            },
            
            # ── 規則 10: 防爬蟲攔截（Info 級別）──
            {
                "rule_id": "RULE-010",
                "type": AnomalyType.BOT_DETECTED,
                "severity": Severity.INFO,
                "confidence": 100,
                "condition": lambda s: s.bot_detected or s.waf_blocked,
                "description_template": "被 WAF/Cloudflare 暫時阻擋，這是網站安全機制正常運作",
                "fix_template": "將 CartRescue IP 段加入白名單，或使用住宅代理",
            },
        ]
    
    def evaluate(self, state: AuditState) -> List[AnomalyResult]:
        """
        對單一 AuditState 執行所有規則，回傳觸發的異常列表
        """
        results = []
        for rule in self.rules:
            try:
                if rule["condition"](state):
                    # 填充模板
                    desc = self._format_template(rule["description_template"], state)
                    fix = self._format_template(rule["fix_template"], state)
                    
                    result = AnomalyResult(
                        anomaly_detected=True,
                        type=rule["type"].value,
                        severity=rule["severity"].value,
                        confidence=rule["confidence"],
                        description=desc,
                        suggested_fix=fix,
                        rule_id=rule["rule_id"],
                        evidence=self._build_evidence(state, rule)
                    )
                    results.append(result)
            except Exception as e:
                # 規則執行錯誤不應中斷整個引擎
                continue
        
        return results
    
    def _format_template(self, template: str, state: AuditState) -> str:
        """填充描述模板"""
        try:
            return template.format(
                subtotal=state.subtotal or 0,
                discount=state.discount_amount or 0,
                total=state.total or 0,
                tax=state.tax_amount or 0,
                product_price=state.product_page_price or 0,
                checkout_price=state.subtotal or 0,
                code=state.discount_code_entered or "未知",
                status=state.http_status or "N/A",
                load_time=state.page_load_time or 0,
                elements=", ".join(state.element_ids_missing[:3]) if state.element_ids_missing else "關鍵元素",
            )
        except Exception:
            return template
    
    def _build_evidence(self, state: AuditState, rule: Dict) -> Dict:
        """建構證據物件"""
        return {
            "url": state.url,
            "step": state.step_name,
            "prices": {
                "subtotal": state.subtotal,
                "discount": state.discount_amount,
                "total": state.total,
                "tax": state.tax_amount,
                "product_page": state.product_page_price,
            },
            "performance": {
                "load_time": state.page_load_time,
                "http_status": state.http_status,
            },
            "errors": {
                "js_errors": state.js_errors[:5],
                "console_errors": state.console_errors[:5],
            },
            "page_text_snippet": state.page_text[:200] if state.page_text else "",
        }
    
    def evaluate_with_timing(self, state: AuditState) -> Dict:
        """帶計時的評估，方便基準測試"""
        start = time.time()
        results = self.evaluate(state)
        elapsed = time.time() - start
        
        return {
            "elapsed_ms": round(elapsed * 1000, 3),
            "anomalies_found": len(results),
            "anomalies": [self._result_to_dict(r) for r in results]
        }
    
    @staticmethod
    def _result_to_dict(result: AnomalyResult) -> Dict:
        return {
            "anomaly_detected": result.anomaly_detected,
            "type": result.type,
            "severity": result.severity,
            "confidence": result.confidence,
            "description": result.description,
            "suggested_fix": result.suggested_fix,
            "rule_id": result.rule_id,
            "detected_at": result.detected_at,
            "evidence": result.evidence,
        }


# ═══════════════════════════════════════════════════════
# 單元測試
# ═══════════════════════════════════════════════════════

def run_tests():
    """執行規則引擎單元測試"""
    print("=" * 60)
    print("CartRescue Rule Engine 單元測試")
    print("=" * 60)
    
    engine = RuleEngine()
    total_tests = 0
    passed = 0
    
    # 測試 1: 折扣計算錯誤
    print("\n[測試 1] 折扣計算錯誤")
    state = AuditState(
        subtotal=3580,
        discount_amount=500,
        total=3200,  # 錯誤：應為 3080
        url="https://example.com/checkout"
    )
    result = engine.evaluate_with_timing(state)
    print(f"  耗時: {result['elapsed_ms']:.3f}ms")
    print(f"  異常數: {result['anomalies_found']}")
    assert result['anomalies_found'] == 1
    assert result['anomalies'][0]['type'] == 'discount_calculation_error'
    assert result['anomalies'][0]['confidence'] == 100
    print(f"  ✅ 通過: {result['anomalies'][0]['description']}")
    total_tests += 1
    passed += 1
    
    # 測試 2: 折扣碼未生效
    print("\n[測試 2] 折扣碼未生效")
    state = AuditState(
        subtotal=3580,
        discount_amount=0,
        total=3580,
        discount_code_entered="SUMMER20",
        discount_error_message="此折扣碼不適用於您的購物車",
        page_text="此折扣碼不適用於您的購物車",
        url="https://travelplus.com.tw/checkout"
    )
    result = engine.evaluate_with_timing(state)
    print(f"  耗時: {result['elapsed_ms']:.3f}ms")
    assert result['anomalies_found'] == 1
    assert result['anomalies'][0]['type'] == 'discount_not_applied'
    print(f"  ✅ 通過: {result['anomalies'][0]['description']}")
    total_tests += 1
    passed += 1
    
    # 測試 3: 支付超時
    print("\n[測試 3] 支付頁面超時")
    state = AuditState(
        step_name="payment",
        page_load_time=45.5,
        url="https://example.com/checkout/payment"
    )
    result = engine.evaluate_with_timing(state)
    print(f"  耗時: {result['elapsed_ms']:.3f}ms")
    assert result['anomalies_found'] == 1
    assert result['anomalies'][0]['type'] == 'payment_timeout'
    print(f"  ✅ 通過: {result['anomalies'][0]['description']}")
    total_tests += 1
    passed += 1
    
    # 測試 4: 正常結帳（無異常）
    print("\n[測試 4] 正常結帳（無異常）")
    state = AuditState(
        subtotal=3580,
        discount_amount=500,
        total=3080,
        discount_code_entered="SUMMER20",
        page_load_time=2.5,
        http_status=200,
        url="https://example.com/checkout"
    )
    result = engine.evaluate_with_timing(state)
    print(f"  耗時: {result['elapsed_ms']:.3f}ms")
    assert result['anomalies_found'] == 0
    print(f"  ✅ 通過: 無異常")
    total_tests += 1
    passed += 1
    
    # 測試 5: 登入牆（Info 級別）
    print("\n[測試 5] 登入牆（預期行為）")
    state = AuditState(
        login_required_detected=True,
        url="https://travelplus.com.tw/login.aspx"
    )
    result = engine.evaluate_with_timing(state)
    print(f"  耗時: {result['elapsed_ms']:.3f}ms")
    assert result['anomalies_found'] == 1
    assert result['anomalies'][0]['type'] == 'login_required'
    assert result['anomalies'][0]['severity'] == 'info'
    print(f"  ✅ 通過: {result['anomalies'][0]['description']}")
    total_tests += 1
    passed += 1
    
    # 測試 6: 多異常同時觸發
    print("\n[測試 6] 多異常同時觸發")
    state = AuditState(
        subtotal=3580,
        discount_amount=0,
        total=3580,
        discount_code_entered="SUMMER20",
        discount_error_message="無效",
        page_text="此折扣碼無效",
        page_load_time=50.0,
        step_name="payment",
        http_status=500,
        url="https://example.com/checkout"
    )
    result = engine.evaluate_with_timing(state)
    print(f"  耗時: {result['elapsed_ms']:.3f}ms")
    print(f"  異常數: {result['anomalies_found']}")
    types_found = [a['type'] for a in result['anomalies']]
    assert 'discount_not_applied' in types_found
    assert 'payment_timeout' in types_found
    assert 'checkout_page_error' in types_found
    print(f"  ✅ 通過: 同時觸發 {len(types_found)} 種異常")
    total_tests += 1
    passed += 1
    
    # 總結
    print(f"\n{'=' * 60}")
    print(f"測試總結: {passed}/{total_tests} 通過")
    print(f"{'=' * 60}")
    
    return passed == total_tests

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
