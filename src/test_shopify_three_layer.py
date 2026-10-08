#!/usr/bin/env python3
"""
CartRescue AI — Shopify 三層架結帳流程驗證腳本
目標網站: https://jeffreestarcosmetics.com (真實 Shopify 商店，無登入牆)
測試流程: 產品頁 → 加入購物車 → 前往結帳 → 輸入折扣碼 → 規則引擎異常檢測

驗證規則:
  RULE-001 折扣計算錯誤 (模擬)
  RULE-002 折扣碼未生效 (故意輸入無效折扣碼)
  RULE-003 支付超時 (模擬)
  RULE-005 價格不一致 (比對商品頁與結帳頁價格)

用法:
  python3 src/test_shopify_three_layer.py
"""
import asyncio, sys, time, re, json, os
from datetime import datetime
from playwright.async_api import async_playwright

sys.path.insert(0, '/home/cartrescue/CartRescue_AI/src')
from rule_engine import RuleEngine, AuditState

# ═══════════════════════════════════════════════════════
# 設定
# ═══════════════════════════════════════════════════════
TARGET_URL = "https://jeffreestarcosmetics.com/products/the-gloss"
PRODUCT_NAME = "The Gloss"
STORE_NAME = "Jeffree Star Cosmetics (Shopify)"
HEADLESS = True

# ═══════════════════════════════════════════════════════
# 工具函式
# ═══════════════════════════════════════════════════════

def extract_dollar_amounts(text: str) -> list[float]:
    """從文字提取所有美元金額"""
    matches = re.findall(r'\$([\d,]+\.\d{2})', text)
    return [float(m.replace(',', '')) for m in matches]


def extract_meta_price(page) -> float | None:
    """從 meta tag 提取商品價格"""
    return page.evaluate('''() => {
        const meta = document.querySelector('meta[property="og:price:amount"]');
        return meta ? meta.content : null;
    }''')


async def capture_state(page, step_name: str, product_price: float | None = None) -> AuditState:
    """從當前頁面建立 AuditState"""
    text = await page.evaluate('() => document.body.innerText')
    amounts = extract_dollar_amounts(text)

    # 判斷 subtotal / total
    subtotal = amounts[0] if amounts else None
    total = amounts[-1] if amounts else None

    state = AuditState(
        url=page.url,
        page_title=await page.title(),
        step_name=step_name,
        page_text=text[:3000],
        subtotal=subtotal,
        total=total,
        discount_amount=0.0,
        product_page_price=product_price,
    )
    return state


# ═══════════════════════════════════════════════════════
# 測試情境
# ═══════════════════════════════════════════════════════

async def run_checkout_flow() -> dict:
    """執行完整結帳流程並回傳所有測試結果"""
    results = {
        "store": STORE_NAME,
        "product": PRODUCT_NAME,
        "target_url": TARGET_URL,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "tests": {},
        "anomalies": [],
        "screenshots": [],
    }
    engine = RuleEngine()
    anomalies = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        # ── Step 1: 訪問產品頁 ──
        print("=" * 60)
        print("[Step 1] 訪問產品頁")
        print("=" * 60)
        t0 = time.time()
        await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
        step1_time = time.time() - t0
        print(f"  載入時間: {step1_time:.2f}s")
        print(f"  標題: {await page.title()}")

        # 提取商品頁價格
        raw_price = await extract_meta_price(page)
        product_price = float(raw_price) if raw_price else None
        print(f"  商品價格: ${product_price}")
        results["product_price"] = product_price
        results["tests"]["step1_product_page"] = {
            "status": "passed",
            "load_time_s": round(step1_time, 2),
            "price": product_price,
        }

        # ── Step 2: 加入購物車 ──
        print("\n" + "=" * 60)
        print("[Step 2] 加入購物車")
        print("=" * 60)
        t0 = time.time()
        add_cart = await page.query_selector('button:has-text("ADD TO CART")')
        if add_cart:
            await add_cart.click()
            await asyncio.sleep(3)
            print("  ✅ 已點擊 ADD TO CART")
            step2_status = "passed"
        else:
            print("  ❌ 找不到加入購物車按鈕")
            step2_status = "failed"
        step2_time = time.time() - t0
        results["tests"]["step2_add_to_cart"] = {
            "status": step2_status,
            "load_time_s": round(step2_time, 2),
        }

        # ── Step 3: 前往結帳 ──
        print("\n" + "=" * 60)
        print("[Step 3] 前往結帳頁")
        print("=" * 60)
        t0 = time.time()
        await page.goto("https://jeffreestarcosmetics.com/checkout",
                        wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        step3_time = time.time() - t0
        print(f"  結帳 URL: {page.url}")
        print(f"  載入時間: {step3_time:.2f}s")
        results["tests"]["step3_checkout"] = {
            "status": "passed",
            "load_time_s": round(step3_time, 2),
            "checkout_url": page.url,
        }

        # 提取結帳頁資訊
        checkout_text = await page.evaluate('() => document.body.innerText')
        amounts = extract_dollar_amounts(checkout_text)
        print(f"  頁面金額: {amounts}")
        results["checkout_amounts"] = amounts

        # ── Step 4: 輸入無效折扣碼 (RULE-002) ──
        print("\n" + "=" * 60)
        print("[Step 4] 測試無效折扣碼 (RULE-002: 折扣碼未生效)")
        print("=" * 60)
        discount_input = await page.query_selector('#checkout_reduction_code') or \
                        await page.query_selector('input[name*="reduction"]') or \
                        await page.query_selector('input[placeholder*="discount" i]')

        rule002_detected = False
        if discount_input:
            await discount_input.fill("INVALIDCODE123")
            await asyncio.sleep(0.5)
            apply_btn = await page.query_selector('button:has-text("Apply")') or \
                       await page.query_selector('button[type="submit"]')
            if apply_btn:
                await apply_btn.click()
                await asyncio.sleep(3)
                print("  ✅ 已輸入無效折扣碼並點擊 Apply")

                text_after = await page.evaluate('() => document.body.innerText')
                error_keywords = ['invalid', "doesn't exist", 'not valid', 'expired',
                                 'unavailable', 'does not exist', 'enter a valid',
                                 'code is not valid']
                rule002_detected = any(kw in text_after.lower() for kw in error_keywords)

                if rule002_detected:
                    lines = text_after.split('\n')
                    for line in lines:
                        if any(kw in line.lower() for kw in error_keywords) and len(line.strip()) > 5:
                            print(f"  🔔 Shopify 回傳錯誤: {line.strip()[:120]}")
                            break
                else:
                    print("  ⚠️ 未發現明確錯誤訊息（折扣碼可能無反應）")
        else:
            print("  ❌ 找不到折扣碼輸入框")

        results["tests"]["rule_002_discount_not_applied"] = {
            "rule_id": "RULE-002",
            "status": "detected" if rule002_detected else "not_detected",
            "description": "折扣碼 INVALIDCODE123 未生效，Shopify 回傳錯誤訊息",
            "expected": True,
            "actual": rule002_detected,
        }

        # ── Step 5: 規則引擎評估 ──
        print("\n" + "=" * 60)
        print("[Step 5] 三層架構規則引擎評估")
        print("=" * 60)

        # 5A: RULE-005 價格不一致
        print("\n  ┌─ [RULE-005] 價格一致性檢查")
        state_r5 = await capture_state(page, "checkout_price_check", product_price)
        r5 = engine.evaluate_with_timing(state_r5)
        print(f"  │  耗時: {r5['elapsed_ms']:.3f}ms")
        print(f"  │  異常數: {r5['anomalies_found']}")
        for a in r5['anomalies']:
            print(f"  │  ⚠️  [{a['severity'].upper()}] {a['description']}")
            anomalies.append(a)
        if r5['anomalies_found'] == 0:
            print(f"  │  ✅ 價格一致，無異常")
        results["tests"]["rule_005_price_mismatch"] = {
            "rule_id": "RULE-005",
            "status": "passed" if r5['anomalies_found'] == 0 else "failed",
            "elapsed_ms": r5['elapsed_ms'],
            "anomalies_found": r5['anomalies_found'],
            "anomalies": r5['anomalies'],
        }

        # 5B: RULE-002 折扣碼未生效（用 AuditState 重新評估）
        print("\n  ┌─ [RULE-002] 折扣碼未生效檢查")
        state_r2 = AuditState(
            url=page.url,
            page_title=await page.title(),
            step_name="checkout_discount",
            subtotal=amounts[0] if amounts else None,
            total=amounts[-1] if amounts else None,
            discount_amount=0.0,
            discount_code_entered="INVALIDCODE123",
            discount_error_message="Enter a valid discount code or gift card" if rule002_detected else None,
            page_text=checkout_text[:3000],
        )
        r2 = engine.evaluate_with_timing(state_r2)
        print(f"  │  耗時: {r2['elapsed_ms']:.3f}ms")
        print(f"  │  異常數: {r2['anomalies_found']}")
        for a in r2['anomalies']:
            print(f"  │  ⚠️  [{a['severity'].upper()}] {a['description']}")
            anomalies.append(a)
        results["tests"]["rule_002_engine_eval"] = {
            "rule_id": "RULE-002",
            "status": "passed" if r2['anomalies_found'] > 0 else "failed",
            "elapsed_ms": r2['elapsed_ms'],
            "anomalies_found": r2['anomalies_found'],
            "anomalies": r2['anomalies'],
        }

        # 5C: RULE-001 折扣計算錯誤（模擬情境：假設折扣碼應折 $5 但系統未扣）
        print("\n  ┌─ [RULE-001] 折扣計算錯誤（模擬情境）")
        simulated_subtotal = amounts[0] if amounts else 22.0
        state_r1 = AuditState(
            url=page.url,
            page_title=await page.title(),
            step_name="checkout_discount_simulation",
            subtotal=simulated_subtotal,
            discount_amount=0.0,   # 假設應有折扣但沒有
            total=simulated_subtotal,
            discount_code_entered="PROMO50",
            page_text="",
        )
        # 手動觸發 RULE-001：subtotal - discount != total（故意製造不一致）
        state_r1.total = simulated_subtotal + 5.0  # 模擬計算錯誤
        r1 = engine.evaluate_with_timing(state_r1)
        print(f"  │  模擬情境: 小計 ${simulated_subtotal} - 折扣 $0 ≠ 總額 ${state_r1.total}")
        print(f"  │  耗時: {r1['elapsed_ms']:.3f}ms")
        print(f"  │  異常數: {r1['anomalies_found']}")
        for a in r1['anomalies']:
            print(f"  │  ⚠️  [{a['severity'].upper()}] {a['description']}")
            anomalies.append(a)
        results["tests"]["rule_001_discount_calculation"] = {
            "rule_id": "RULE-001",
            "status": "passed" if r1['anomalies_found'] > 0 else "failed",
            "elapsed_ms": r1['elapsed_ms'],
            "anomalies_found": r1['anomalies_found'],
            "anomalies": r1['anomalies'],
        }

        # 5D: RULE-003 支付超時（模擬情境）
        print("\n  ┌─ [RULE-003] 支付超時（模擬情境）")
        state_r3 = AuditState(
            url=page.url,
            page_title=await page.title(),
            step_name="payment",
            page_load_time=45.5,  # 模擬超過 30 秒
        )
        r3 = engine.evaluate_with_timing(state_r3)
        print(f"  │  模擬情境: 支付頁面載入 45.5 秒")
        print(f"  │  耗時: {r3['elapsed_ms']:.3f}ms")
        print(f"  │  異常數: {r3['anomalies_found']}")
        for a in r3['anomalies']:
            print(f"  │  ⚠️  [{a['severity'].upper()}] {a['description']}")
            anomalies.append(a)
        results["tests"]["rule_003_payment_timeout"] = {
            "rule_id": "RULE-003",
            "status": "passed" if r3['anomalies_found'] > 0 else "failed",
            "elapsed_ms": r3['elapsed_ms'],
            "anomalies_found": r3['anomalies_found'],
            "anomalies": r3['anomalies'],
        }

        # ── Step 6: 截圖 ──
        print("\n" + "=" * 60)
        print("[Step 6] 截圖存檔")
        print("=" * 60)
        screenshot_dir = "/home/cartrescue/CartRescue_AI/src/screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        ts = int(time.time())
        ss_path = f"{screenshot_dir}/shopify_checkout_{ts}.png"
        await page.screenshot(path=ss_path, full_page=True)
        print(f"  📸 截圖: {ss_path}")
        results["screenshots"].append(ss_path)

        await browser.close()

    # ── 總結 ──
    results["ended_at"] = datetime.utcnow().isoformat() + "Z"
    results["anomalies"] = anomalies
    return results


# ═══════════════════════════════════════════════════════
# 主程式
# ═══════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 60)
    print("CartRescue AI — Shopify 三層架結帳流程驗證")
    print(f"目標: {STORE_NAME}")
    print("=" * 60 + "\n")

    results = asyncio.run(run_checkout_flow())

    # 輸出摘要
    print("\n" + "=" * 60)
    print("測試摘要")
    print("=" * 60)

    total = 0
    passed = 0
    for name, test in results["tests"].items():
        status = test.get("status", "unknown")
        total += 1
        if status in ("passed", "detected"):
            passed += 1
            icon = "✅"
        elif status in ("failed", "not_detected"):
            icon = "❌"
        else:
            icon = "⚠️"
        print(f"  {icon} {name:<35s} | {status}")

    print(f"\n  通過率: {passed}/{total}")
    print(f"  異常總數: {len(results['anomalies'])}")
    print(f"  截圖: {results['screenshots']}")

    # 儲存 JSON 結果
    report_path = "/home/cartrescue/CartRescue_AI/research/shopify_three_layer_results.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  結果 JSON 已儲存: {report_path}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
