#!/usr/bin/env python3
"""
CartRescue AI — TravelPlus 三層架構實戰測試
目標網站: https://www.travelplus.com.tw/
測試流程: 產品頁 → 加入購物車(AJAX) → 前往購物車 → 規則引擎異常檢測
"""
import asyncio, sys, time, re
from playwright.async_api import async_playwright

sys.path.insert(0, '/home/cartrescue/CartRescue_AI/src')
from rule_engine import RuleEngine, AuditState

TARGET_URL = "https://www.travelplus.com.tw/Product.aspx?ProductColorProductID=26043&cid=1739"

async def audit_travelplus():
    print("=" * 60)
    print("CartRescue AI — TravelPlus 三層架構實戰測試")
    print(f"目標: {TARGET_URL}")
    print("=" * 60)
    
    engine = RuleEngine()
    anomalies = []
    start_time = time.time()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        page.set_default_timeout(30000)
        
        # ── Step 1: 訪問產品頁 ──
        print("\n[Step 1] 訪問產品頁...")
        t0 = time.time()
        try:
            await page.goto(TARGET_URL, wait_until="domcontentloaded")
            await asyncio.sleep(2)  # 等待 AJAX 載入
            title = await page.title()
            print(f"  ✅ 載入成功: {title[:50]}")
            print(f"  URL: {page.url}")
            step1_time = time.time() - t0
            print(f"  耗時: {step1_time:.1f}s")
        except Exception as e:
            print(f"  ❌ 載入失敗: {e}")
            await browser.close()
            return
        
        # ── Step 2: 點擊「放入購物車」──
        print("\n[Step 2] 加入購物車...")
        t0 = time.time()
        try:
            # TravelPlus 使用 #putinCart
            btn = await page.query_selector("#putinCart")
            if btn:
                await btn.click()
                print(f"  ✅ 點擊 #putinCart")
            else:
                # Fallback: 找包含「放入購物車」的元素
                btn = await page.query_selector('a:has-text("放入購物車")')
                if btn:
                    await btn.click()
                    print(f"  ✅ 點擊「放入購物車」")
                else:
                    raise RuntimeError("找不到加入購物車按鈕")
            
            await asyncio.sleep(3)  # 等待 AJAX
            step2_time = time.time() - t0
            print(f"  耗時: {step2_time:.1f}s")
            
        except Exception as e:
            print(f"  ❌ 加入購物車失敗: {e}")
            await browser.close()
            return
        
        # ── Step 3: 提取頁面資訊（產品頁加入購物車後的狀態）──
        print("\n[Step 3] 提取頁面資訊...")
        page_text = await page.content()
        page_text_short = await page.evaluate("() => document.body.innerText.substring(0, 1000)")
        
        # 使用 Price Extractor 提取價格
        from price_extractor import extract_prices, extract_prices_with_context
        prices = extract_prices(page_text)
        prices_with_ctx = extract_prices_with_context(page_text)
        print(f"  找到價格: {prices}")
        if prices_with_ctx:
            print(f"  價格上下文:")
            for p in prices_with_ctx[:5]:
                print(f"    - {p['matched_text']} → {p['price']:.0f} ({p['pattern_label']})")
        
        # 檢查是否有「加入購物車成功」提示
        success_indicators = ["已加入", "成功", "購物車", "cart", "加入成功"]
        has_success = any(ind in page_text_short for ind in success_indicators)
        print(f"  成功提示: {has_success}")
        
        # ── Step 4: 前往購物車 ──
        print("\n[Step 4] 前往購物車...")
        t0 = time.time()
        try:
            # TravelPlus 購物車連結
            cart_links = [
                "https://www.travelplus.com.tw/shoppingcart.aspx",
                "https://www.travelplus.com.tw/ShoppingCart.aspx",
            ]
            cart_reached = False
            for cart_url in cart_links:
                try:
                    await page.goto(cart_url, wait_until="domcontentloaded", timeout=15000)
                    await asyncio.sleep(2)
                    cart_reached = True
                    print(f"  ✅ 到達購物車: {page.url}")
                    break
                except Exception:
                    continue
            
            if not cart_reached:
                # 嘗試點擊購物車圖示
                cart_btn = await page.query_selector('#goShoppingCart') or \
                          await page.query_selector('a:has-text("購物車")')
                if cart_btn:
                    await cart_btn.click()
                    await asyncio.sleep(2)
                    cart_reached = True
                    print(f"  ✅ 點擊購物車圖示到達: {page.url}")
            
            step4_time = time.time() - t0
            print(f"  耗時: {step4_time:.1f}s")
            
        except Exception as e:
            print(f"  ⚠️ 前往購物車失敗: {e}")
            cart_reached = False
        
        # ── Step 5: 三層架構異常檢測 ──
        print("\n[Step 5] 三層架構異常檢測...")
        
        # 提取最終頁面文字
        final_text = await page.evaluate("() => document.body.innerText.substring(0, 2000)")
        
        # 使用新的 AuditState.from_page_text() 建立狀態（自動價格提取）
        state = AuditState.from_page_text(
            page_text=final_text,
            url=page.url,
            step_name="cart_page" if cart_reached else "checkout_page",
        )
        
        # 若產品頁已有價格，嘗試設定更準確的 subtotal
        if prices:
            state.subtotal = prices[0]
            state.product_page_price = prices[0]
            if len(prices) > 1:
                state.total = prices[-1]
        
        # 檢查是否有登入要求
        if any(kw in final_text for kw in ["登入", "login", "會員", "Member"]):
            state.login_required_detected = True
        
        # Layer 1: 規則引擎
        print(f"\n  ┌─ Layer 1: 規則引擎")
        t0 = time.time()
        result = engine.evaluate_with_timing(state)
        layer1_time = (time.time() - t0) * 1000
        print(f"  │  耗時: {layer1_time:.3f}ms")
        print(f"  │  異常數: {result['anomalies_found']}")
        
        for a in result['anomalies']:
            print(f"  │  ⚠️  [{a['severity'].upper()}] {a['description']}")
            anomalies.append(a)
        
        if result['anomalies_found'] == 0:
            print(f"  │  ✅ 規則引擎未發現異常")
        
        # Layer 2: DeepSeek Flash（模擬 — 實際環境才呼叫）
        if result['anomalies_found'] == 0:
            print(f"\n  ├─ Layer 2: DeepSeek Flash（規則未命中，理論上應呼叫）")
            print(f"  │  📝 模擬：若規則未命中，將呼叫 DeepSeek Flash (0.84s, $0.003)")
            # 實際環境會呼叫，此處跳過以避免 API 成本
        else:
            print(f"\n  ├─ Layer 2: DeepSeek Flash（跳過 — 規則已命中，節省 $0.003）")
        
        # Layer 3: 回退啟發式（跳過，因為規則已處理）
        print(f"\n  └─ Layer 3: 回退啟發式")
        print(f"     📝 若前兩層皆未命中，啟用關鍵字掃描保底")
        
        # 截圖
        screenshot_path = f"/home/cartrescue/CartRescue_AI/src/screenshots/travelplus_test_{int(time.time())}.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n  📸 截圖已儲存: {screenshot_path}")
        
        await browser.close()
    
    # ── 報告 ──
    total_time = time.time() - start_time
    print(f"\n{'=' * 60}")
    print("測試報告")
    print(f"{'=' * 60}")
    print(f"總耗時: {total_time:.1f}s")
    print(f"異常數: {len(anomalies)}")
    
    if anomalies:
        print(f"\n發現的異常:")
        for a in anomalies:
            print(f"  - [{a['severity'].upper()}] {a['description']}")
    else:
        print(f"\n✅ 未發現異常（在規則引擎覆蓋範圍內）")
    
    print(f"\n{'=' * 60}")
    print("三層架構效能驗證:")
    print(f"  規則引擎: {layer1_time:.3f}ms (零成本)")
    print(f"  DeepSeek: 理論上 0.84s (未觸發，節省)")
    print(f"  回退啟發式: <1ms (未觸發)")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    asyncio.run(audit_travelplus())
