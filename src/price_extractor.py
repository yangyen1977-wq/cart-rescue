#!/usr/bin/env python3
"""
CartRescue AI — 全球電商價格提取模組（Price Extractor v1）
用途：從各種電商網站頁面文字中，提取標準化價格數值

設計哲學：
- 多模式正則匹配，覆蓋全球主流貨幣格式
- 支援前綴、後綴、純數字、中文標示
- 輸出統一為 float（已移除貨幣符號與千分位逗號）
- 自動過濾過小數值（< 10），避免提取年份、數量等雜訊

論文依據：
- WebTestPilot (2602.11724): 從 GUI 文字中提取結構化數值
"""

import re
from typing import List, Tuple


# ═══════════════════════════════════════════════════════
# 價格格式正則表達式庫
# ═══════════════════════════════════════════════════════

PRICE_PATTERNS: List[Tuple[str, str]] = [
    # ── 新台幣 / 台幣（繁體中文電商主流）──
    (r'NT\$\s*([\d,]+(?:\.\d{1,2})?)',          'NT$前綴'),
    (r'台幣\s*([\d,]+(?:\.\d{1,2})?)',          '台幣前綴'),
    (r'新台幣\s*([\d,]+(?:\.\d{1,2})?)',        '新台幣前綴'),
    (r'TWD\s*([\d,]+(?:\.\d{1,2})?)',           'TWD前綴'),
    (r'([\d,]+(?:\.\d{1,2})?)\s*NT',            'NT後綴'),
    (r'([\d,]+(?:\.\d{1,2})?)\s*TWD',           'TWD後綴'),

    # ── 美元（國際電商主流）──
    (r'US\$\s*([\d,]+(?:\.\d{1,2})?)',          'US$前綴'),
    (r'USD\s*([\d,]+(?:\.\d{1,2})?)',           'USD前綴'),
    (r'\$\s*([\d,]+(?:\.\d{1,2})?)',            '$前綴（通用）'),
    (r'([\d,]+(?:\.\d{1,2})?)\s*USD',           'USD後綴'),

    # ── 歐元（歐洲電商）──
    (r'€\s*([\d,]+(?:\.\d{1,2})?)',             '€前綴'),
    (r'EUR\s*([\d,]+(?:\.\d{1,2})?)',           'EUR前綴'),
    (r'([\d,]+(?:\.\d{1,2})?)\s*€',             '€後綴'),
    (r'([\d,]+(?:\.\d{1,2})?)\s*EUR',           'EUR後綴'),

    # ── 日元 / 人民幣（亞洲電商）──
    (r'¥\s*([\d,]+(?:\.\d{1,2})?)',             '¥前綴'),
    (r'JPY\s*([\d,]+(?:\.\d{1,2})?)',            'JPY前綴'),
    (r'CNY\s*([\d,]+(?:\.\d{1,2})?)',            'CNY前綴'),
    (r'RMB\s*([\d,]+(?:\.\d{1,2})?)',            'RMB前綴'),
    (r'([\d,]+(?:\.\d{1,2})?)\s*¥',             '¥後綴'),

    # ── 英鎊（英國電商）──
    (r'£\s*([\d,]+(?:\.\d{1,2})?)',             '£前綴'),
    (r'GBP\s*([\d,]+(?:\.\d{1,2})?)',            'GBP前綴'),
    (r'([\d,]+(?:\.\d{1,2})?)\s*£',             '£後綴'),

    # ── 韓元（韓國電商）──
    (r'₩\s*([\d,]+(?:\.\d{1,2})?)',             '₩前綴'),
    (r'KRW\s*([\d,]+(?:\.\d{1,2})?)',            'KRW前綴'),

    # ── 泰銖（東南亞電商）──
    (r'฿\s*([\d,]+(?:\.\d{1,2})?)',             '฿前綴'),
    (r'THB\s*([\d,]+(?:\.\d{1,2})?)',            'THB前綴'),

    # ── 澳幣 / 加幣 / 港幣 ──
    (r'A\$\s*([\d,]+(?:\.\d{1,2})?)',           'A$前綴'),
    (r'AU\$\s*([\d,]+(?:\.\d{1,2})?)',           'AU$前綴'),
    (r'CAD\s*([\d,]+(?:\.\d{1,2})?)',            'CAD前綴'),
    (r'HK\$\s*([\d,]+(?:\.\d{1,2})?)',           'HK$前綴'),
    (r'HKD\s*([\d,]+(?:\.\d{1,2})?)',            'HKD前綴'),

    # ── 中文「價格」標示（台灣/中國電商常見）──
    (r'[價格售價特價原價促銷價]\s*[：:]\s*([\d,]+(?:\.\d{1,2})?)',  '中文價格標示'),
    (r'[價格售價特價]\s+([\d,]+(?:\.\d{1,2})?)',                  '中文價格空格'),

    # ── 英文 Price 標示（Amazon / eBay / Shopify）──
    (r'[Pp]rice\s*[：:]\s*([\d,]+(?:\.\d{1,2})?)',               'Price標示'),
    (r'[Pp]rice\s+([\d,]+(?:\.\d{1,2})?)',                        'Price空格'),

    # ── 日文「円」「価格」標示──
    (r'([\d,]+(?:\.\d{1,2})?)\s*円',             '日元後綴（円）'),
    (r'([\d,]+(?:\.\d{1,2})?)\s*원',             '韓元後綴（원）'),
    (r'([\d,]+(?:\.\d{1,2})?)\s*元',             '人民幣/台幣後綴（元）'),

    # ── 純數字兜底（大於 10 的千分位數字，避免提取年份）──
    # 標準千分位格式（如 1,000 或 1,000,000），要求逗號在正確位置
    (r'(?<!\d|,)\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?(?!\d|,)',  '純數字（標準千分位）'),
    # 無逗號純數字（至少 4 位，避免提取年份如 2024）
    (r'(?<!\d)\d{4,}(?:\.\d{1,2})?(?!\d)',                  '純數字（無逗號）'),
]


def _parse_price(raw: str) -> float:
    """
    將匹配到的原始價格字串轉為標準 float
    - 移除逗號（千分位符號）
    - 保留小數點
    """
    cleaned = raw.replace(',', '').strip()
    return float(cleaned)


def extract_prices(text: str, min_value: float = 10.0) -> List[float]:
    """
    從文字中提取所有價格數值。

    參數:
        text:      輸入文字（如 HTML innerText 或頁面原始碼）
        min_value: 過濾門檻，小於此值的數字會被忽略（預設 10，排除年份、數量）

    回傳:
        List[float]: 去重後的價格列表，由小到大排序
    """
    if not text:
        return []

    found: set = set()

    for pattern, _label in PRICE_PATTERNS:
        for match in re.finditer(pattern, text):
            # 取得 capture group 或完整匹配值
            try:
                raw = match.group(1)
            except IndexError:
                raw = match.group(0)
            try:
                val = _parse_price(raw)
                if val >= min_value:
                    found.add(val)
            except ValueError:
                continue

    return sorted(found)


def extract_prices_with_context(text: str, min_value: float = 10.0) -> List[dict]:
    """
    進階版：同時回傳價格與其上下文（用於除錯與審計報告）。

    回傳:
        List[dict]: 每項包含 price（float）、matched_text（str）、position（int）
    """
    if not text:
        return []

    results: List[dict] = []
    seen: set = set()

    for pattern, label in PRICE_PATTERNS:
        for match in re.finditer(pattern, text):
            raw = match.group(1)
            try:
                val = _parse_price(raw)
                if val >= min_value and val not in seen:
                    seen.add(val)
                    results.append({
                        "price": val,
                        "matched_text": match.group(0),
                        "position": match.start(),
                        "pattern_label": label,
                    })
            except ValueError:
                continue

    # 按出現位置排序
    results.sort(key=lambda x: x["position"])
    return results


def extract_single_price(text: str, min_value: float = 10.0) -> float:
    """
    便捷函數：提取第一個（通常是最左邊）價格。
    若無匹配則回傳 0.0。
    """
    prices = extract_prices(text, min_value)
    return prices[0] if prices else 0.0


# ═══════════════════════════════════════════════════════
# 單元測試
# ═══════════════════════════════════════════════════════

def _test_case(description: str, text: str, expected: List[float], min_value: float = 10.0) -> bool:
    """執行單一測試案例並輸出結果。"""
    result = extract_prices(text, min_value)
    passed = result == expected
    status = "✅ 通過" if passed else "❌ 失敗"
    print(f"  [{status}] {description}")
    if not passed:
        print(f"      輸入: {text!r}")
        print(f"      預期: {expected}")
        print(f"      實際: {result}")
    return passed


def run_tests():
    """執行 Price Extractor 單元測試，覆蓋所有支援格式。"""
    print("=" * 60)
    print("CartRescue Price Extractor 單元測試")
    print("=" * 60)

    total = 0
    passed = 0

    # ── 1. 新台幣格式 ──
    total += 1; passed += _test_case(
        "NT$前綴無空格", "商品價格 NT$3,580", [3580.0]
    )
    total += 1; passed += _test_case(
        "NT$前綴有空格", "特價 NT$ 1,299", [1299.0]
    )
    total += 1; passed += _test_case(
        "NT$含小數", "NT$999.50", [999.5]
    )
    total += 1; passed += _test_case(
        "TWD前綴", "TWD 25,000", [25000.0]
    )
    total += 1; passed += _test_case(
        "台幣前綴", "售價台幣 15,800", [15800.0]
    )
    total += 1; passed += _test_case(
        "新台幣前綴", "原價新台幣 20,000", [20000.0]
    )

    # ── 2. 美元格式 ──
    total += 1; passed += _test_case(
        "US$前綴", "US$199.99", [199.99]
    )
    total += 1; passed += _test_case(
        "USD前綴", "USD 1,500", [1500.0]
    )
    total += 1; passed += _test_case(
        "$前綴", "$49.99", [49.99]
    )
    total += 1; passed += _test_case(
        "$有空格", "$ 899", [899.0]
    )

    # ── 3. 歐元格式 ──
    total += 1; passed += _test_case(
        "€前綴", "€1,299", [1299.0]
    )
    total += 1; passed += _test_case(
        "EUR前綴", "EUR 899.00", [899.0]
    )

    # ── 4. 日元 / 人民幣格式 ──
    total += 1; passed += _test_case(
        "¥前綴", "¥15,800", [15800.0]
    )
    total += 1; passed += _test_case(
        "JPY前綴", "JPY 100,000", [100000.0]
    )
    total += 1; passed += _test_case(
        "CNY前綴", "CNY 3,599", [3599.0]
    )
    total += 1; passed += _test_case(
        "RMB前綴", "RMB 4,999", [4999.0]
    )

    # ── 5. 英鎊格式 ──
    total += 1; passed += _test_case(
        "£前綴", "£799.00", [799.0]
    )
    total += 1; passed += _test_case(
        "GBP前綴", "GBP 1,199", [1199.0]
    )

    # ── 6. 韓元 / 泰銖 ──
    total += 1; passed += _test_case(
        "₩前綴", "₩150,000", [150000.0]
    )
    total += 1; passed += _test_case(
        "KRW前綴", "KRW 250,000", [250000.0]
    )
    total += 1; passed += _test_case(
        "THB前綴", "THB 3,500", [3500.0]
    )

    # ── 7. 澳幣 / 加幣 / 港幣 ──
    total += 1; passed += _test_case(
        "A$前綴", "A$1,200", [1200.0]
    )
    total += 1; passed += _test_case(
        "CAD前綴", "CAD 899", [899.0]
    )
    total += 1; passed += _test_case(
        "HK$前綴", "HK$6,999", [6999.0]
    )

    # ── 8. 中文「價格」標示 ──
    total += 1; passed += _test_case(
        "中文價格：", "價格：2,999", [2999.0]
    )
    total += 1; passed += _test_case(
        "中文售價", "售價 18,900", [18900.0]
    )
    total += 1; passed += _test_case(
        "中文原價", "原價：3,500 特價：2,800", [2800.0, 3500.0]
    )

    # ── 9. 英文 Price 標示 ──
    total += 1; passed += _test_case(
        "Price:", "Price: $199.00", [199.0]
    )
    total += 1; passed += _test_case(
        "price空格", "price 599", [599.0]
    )

    # ── 10. 日文 / 韓文 / 中文後綴 ──
    total += 1; passed += _test_case(
        "日元後綴円", "15,800円", [15800.0]
    )
    total += 1; passed += _test_case(
        "韓元後綴원", "250,000원", [250000.0]
    )
    total += 1; passed += _test_case(
        "中文元後綴", "3,599元", [3599.0]
    )

    # ── 11. 純數字兜底 ──
    total += 1; passed += _test_case(
        "純數字千分位", "促銷價 1,299 起", [1299.0]
    )
    total += 1; passed += _test_case(
        "多價格去重排序", "NT$2,000 特價 1,500 1,500", [1500.0, 2000.0]
    )

    # ── 12. 邊界條件 ──
    total += 1; passed += _test_case(
        "空字串", "", []
    )
    total += 1; passed += _test_case(
        "無價格文字", "歡迎來到本店", []
    )
    total += 1; passed += _test_case(
        "過小數值過濾", "數量 5 個", [], min_value=10.0
    )

    # 總結
    print(f"\n{'=' * 60}")
    print(f"測試總結: {passed}/{total} 通過")
    print(f"{'=' * 60}")
    return passed == total


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
