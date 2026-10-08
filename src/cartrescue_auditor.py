#!/usr/bin/env python3
"""
CartRescue AI — Checkout Auditor
================================
A standalone Playwright + Stagehand (fallback) script that audits e-commerce
checkout flows end-to-end:

    Product Page → Cart → Checkout → Payment Page

Screenshots are saved for every step. A text report is emitted on stdout
(and optionally written to disk).  No real payment is ever submitted.

Usage
-----
    # Pure Playwright (default — no API keys required)
    python cartrescue_auditor.py https://example.com/product/123

    # With Stagehand AI assistance (requires Browserbase API key)
    BROWSERBASE_API_KEY=xxx BROWSERBASE_PROJECT_ID=yyy \
        python cartrescue_auditor.py https://example.com/product/123

Dependencies
------------
    pip install playwright stagehand-py
    playwright install chromium

Exit codes
----------
    0  – audit completed, no anomalies detected
    1  – audit completed, anomalies detected
    2  – fatal error (network, missing deps, etc.)
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Optional Stagehand import — graceful fallback if not installed / no keys
# ---------------------------------------------------------------------------
try:
    import stagehand
    from stagehand import Stagehand, StagehandConfig
    _STAGEHAND_OK = True
except Exception:
    _STAGEHAND_OK = False
    Stagehand = None  # type: ignore

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

# ---------------------------------------------------------------------------
# CartRescue Rule Engine (zero-cost anomaly detection)
# ---------------------------------------------------------------------------
try:
    from rule_engine import RuleEngine, AuditState, Severity, AnomalyType
    _RULE_ENGINE_OK = True
except Exception:
    _RULE_ENGINE_OK = False
    RuleEngine = None  # type: ignore
    AuditState = None  # type: ignore

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_HEADLESS = True
DEFAULT_TIMEOUT_MS = 30_000
STEP_TIMEOUT_MS = 10_000
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
REPORT_DIR = Path(__file__).parent / "reports"

STAGEHAND_SERVER_URL = os.getenv("STAGEHAND_API_URL", "https://api.stagehand.dev")

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Anomaly:
    step: str
    severity: str  # "CRITICAL" | "WARNING" | "INFO"
    message: str
    detail: str = ""

    def __str__(self) -> str:
        return f"[{self.severity}] {self.step}: {self.message}"


@dataclass
class StepResult:
    name: str
    url: str = ""
    screenshot_path: str = ""
    duration_sec: float = 0.0
    success: bool = True
    notes: str = ""


@dataclass
class AuditReport:
    target_url: str
    started_at: str
    finished_at: str = ""
    total_duration_sec: float = 0.0
    steps: list[StepResult] = field(default_factory=list)
    anomalies: list[Anomaly] = field(default_factory=list)

    def to_text(self) -> str:
        lines = [
            "=" * 60,
            "  CartRescue AI — Checkout Audit Report",
            "=" * 60,
            f"  Target URL      : {self.target_url}",
            f"  Started         : {self.started_at}",
            f"  Finished        : {self.finished_at}",
            f"  Total Duration  : {self.total_duration_sec:.1f}s",
            "",
            "  Steps",
            "  " + "-" * 56,
        ]
        for s in self.steps:
            status = "✓" if s.success else "✗"
            lines.append(
                f"    [{status}] {s.name:20s}  {s.duration_sec:.1f}s  {s.url[:40]}"
            )
            if s.notes:
                lines.append(f"         Note: {s.notes}")
        lines += [
            "",
            "  Anomalies",
            "  " + "-" * 56,
        ]
        if self.anomalies:
            for a in self.anomalies:
                lines.append(f"    {a}")
                if a.detail:
                    lines.append(f"       Detail: {a.detail}")
        else:
            lines.append("    None detected — checkout flow looks healthy.")
        lines += ["", "=" * 60]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_dirs() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def _screenshot_path(step_name: str, ts: str) -> Path:
    safe = "".join(c if c.isalnum() else "_" for c in step_name)
    return SCREENSHOT_DIR / f"{ts}_{safe}.png"


def _report_path(ts: str) -> Path:
    return REPORT_DIR / f"audit_{ts}.txt"


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _normalize_url(raw: str) -> str:
    if not raw.startswith(("http://", "https://")):
        return "https://" + raw
    return raw


async def _save_screenshot(page: Page, path: Path) -> None:
    try:
        await page.screenshot(path=str(path), full_page=False)
    except Exception as exc:
        # Fallback to full-page if viewport fails
        await page.screenshot(path=str(path), full_page=True)


async def _detect_anomalies(
    step_name: str, page: Page, page_text: str
) -> list[Anomaly]:
    """Heuristic anomaly detection based on page text and title."""
    anomalies: list[Anomaly] = []
    lower = page_text.lower()
    try:
        title_raw = await page.title()
        title = title_raw.lower()
    except Exception:
        title = ""

    # Error keywords
    error_keywords = [
        "error", "exception", "something went wrong", "failed to load",
        "page not found", "404", "403", "500", "bad request",
    ]
    for kw in error_keywords:
        if kw in lower or kw in title:
            anomalies.append(
                Anomaly(
                    step=step_name,
                    severity="CRITICAL",
                    message=f"Detected error keyword: '{kw}'",
                    detail="Page content or title contains an error indicator.",
                )
            )
            break  # one per step is enough

    # Payment-page specific checks
    if step_name == "payment_page":
        if "ssl" not in lower and "https" not in page.url:
            anomalies.append(
                Anomaly(
                    step=step_name,
                    severity="WARNING",
                    message="Payment page not served over HTTPS",
                    detail=f"URL: {page.url}",
                )
            )
        if "captcha" in lower or "robot" in lower:
            anomalies.append(
                Anomaly(
                    step=step_name,
                    severity="INFO",
                    message="CAPTCHA or bot check detected",
                    detail="This may block automated checkout completion.",
                )
            )

    # Cart-page specific checks
    if step_name == "cart_page":
        if "empty" in lower and "cart" in lower:
            anomalies.append(
                Anomaly(
                    step=step_name,
                    severity="WARNING",
                    message="Cart appears empty after adding item",
                    detail="The item may not have been added successfully.",
                )
            )

    return anomalies


# ---------------------------------------------------------------------------
# CartRescue Rule-Engine + DeepSeek Flash anomaly detection (two-layer)
# ---------------------------------------------------------------------------

async def _extract_audit_state(
    step_name: str, page: Page, page_text: str, start_url: str
) -> Any:
    """Extract symbolised AuditState from a Playwright Page for the rule engine."""
    state = AuditState(
        url=page.url,
        page_title=await page.title() if hasattr(page, 'title') else "",
        step_name=step_name,
        page_text=page_text[:500],
    )
    
    # Try to extract price symbols from page text (heuristic)
    import re
    prices = re.findall(r'NT\$\s*([\d,]+)', page_text)
    if len(prices) >= 1:
        # Last price is usually total, first is subtotal
        clean = lambda s: float(s.replace(',', ''))
        state.subtotal = clean(prices[0]) if prices else None
        state.total = clean(prices[-1]) if len(prices) > 1 else state.subtotal
    
    # Discount amount (if page text shows it)
    discount_match = re.search(r'折扣\s*[：:]\s*NT\$\s*([\d,]+)', page_text)
    if discount_match:
        state.discount_amount = float(discount_match.group(1).replace(',', ''))
    
    # Discount error message
    if any(kw in page_text for kw in ["折扣碼不適用", "無效", "invalid", "not applicable"]):
        state.discount_error_message = "折扣碼不適用或無效"
    
    # HTTP status (from response if available)
    try:
        resp = await page.evaluate("() => { return window.performance.getEntriesByType('navigation')[0]?.responseStatus || 200 }")
        state.http_status = resp
    except Exception:
        state.http_status = 200
    
    # Page load time (from performance API)
    try:
        timing = await page.evaluate("""() => {
            const n = performance.getEntriesByType('navigation')[0];
            return n ? n.loadEventEnd - n.startTime : null;
        }""")
        if timing:
            state.page_load_time = timing / 1000.0
    except Exception:
        pass
    
    # Check for login wall
    if any(kw in page_text.lower() for kw in ["login", "登入", "member", "會員", "註冊"]):
        if any(kw in page_text for kw in ["請先登入", "登入會員", "會員專區", "login required"]):
            state.login_required_detected = True
    
    # Check for CAPTCHA
    if any(kw in page_text.lower() for kw in ["captcha", "驗證碼", "驗證", "安全驗證"]):
        state.captcha_detected = True
    
    # Check for bot/WAF detection
    if any(kw in page_text.lower() for kw in ["access denied", "blocked", "forbidden", "cloudflare", "waf"]):
        state.waf_blocked = True
    
    # JS errors from page console (if we had console listener)
    # For now, check page text for error indicators
    if any(kw in page_text.lower() for kw in ["error", "exception", "500", "something went wrong"]):
        state.js_errors.append("Page text contains error indicator")
    
    return state


async def _detect_anomalies_with_rule_engine(
    step_name: str, page: Page, page_text: str, start_url: str
) -> list[Anomaly]:
    """Two-layer detection: Rule Engine (fast) → DeepSeek Flash (smart)."""
    anomalies: list[Anomaly] = []
    
    # ---- Layer 1: Rule Engine (zero cost, <1ms) ----
    if _RULE_ENGINE_OK:
        engine = RuleEngine()
        state = await _extract_audit_state(step_name, page, page_text, start_url)
        rule_results = engine.evaluate_with_timing(state)
        
        # Convert rule results back to Anomaly dataclass
        for r in rule_results.get("anomalies", []):
            anomalies.append(
                Anomaly(
                    step=step_name,
                    severity=r["severity"].upper(),
                    message=f"[{r['rule_id']}] {r['description']}",
                    detail=f"Fix: {r['suggested_fix']} | Confidence: {r['confidence']}",
                )
            )
    
    # ---- Layer 2: DeepSeek Flash LLM (fast, $0.003) ----
    # Only run if rule engine found nothing AND we're on checkout/payment
    if not anomalies and step_name in ("checkout_page", "payment_page", "cart_page"):
        llm_result = await _detect_anomalies_with_deepseek(step_name, page_text)
        if llm_result:
            anomalies.append(llm_result)
    
    # Fallback: original heuristic detection
    if not anomalies:
        anomalies.extend(await _detect_anomalies(step_name, page, page_text))
    
    return anomalies


async def _detect_anomalies_with_deepseek(
    step_name: str, page_text: str
) -> Optional[Anomaly]:
    """Use DeepSeek v4.1 Flash for lightweight anomaly detection."""
    api_key = os.getenv("OLLAMA_API_KEY")
    if not api_key:
        return None
    
    prompt = f"""你是電商審計AI。根據以下頁面文字判斷是否有異常：

頁面類型: {step_name}
頁面文字: {page_text[:300]}

請只輸出：異常類型（如折扣失效/支付錯誤/無異常）和信心分數（0-100）。
格式: 異常類型 分數"""
    
    try:
        import requests
        resp = requests.post(
            "https://ollama.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-v4.1-flash",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 50,
                "temperature": 0.1
            },
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"].get("content", "")
            if content and "無異常" not in content and "正常" not in content.lower():
                return Anomaly(
                    step=step_name,
                    severity="WARNING",
                    message=f"[DeepSeek] {content.strip()}",
                    detail="LLM-based anomaly detection triggered",
                )
    except Exception:
        pass
    
    return None


# ---------------------------------------------------------------------------
# Core audit logic (pure Playwright — always works)
# ---------------------------------------------------------------------------

async def _audit_with_playwright(
    target_url: str, headless: bool
) -> AuditReport:
    report = AuditReport(
        target_url=target_url,
        started_at=datetime.now().isoformat(),
    )
    anomalies: list[Anomaly] = []
    step_results: list[StepResult] = []
    ts = _timestamp()

    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch(headless=headless)
        context: BrowserContext = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page: Page = await context.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT_MS)

        # ---- Step 1: Product Page ----------------------------------------
        step = StepResult(name="product_page")
        t0 = asyncio.get_event_loop().time()
        try:
            await page.goto(target_url, wait_until="networkidle")
            step.url = page.url
            step.success = True
            step.notes = f"Title: {await page.title()}"
        except Exception as exc:
            step.success = False
            step.notes = f"Failed to load: {exc}"
            anomalies.append(
                Anomaly(
                    step="product_page",
                    severity="CRITICAL",
                    message="Could not load product page",
                    detail=str(exc),
                )
            )
        finally:
            step.duration_sec = asyncio.get_event_loop().time() - t0
            sp = _screenshot_path("product_page", ts)
            await _save_screenshot(page, sp)
            step.screenshot_path = str(sp)
            step_results.append(step)

        if not step.success:
            await browser.close()
            report.steps = step_results
            report.anomalies = anomalies
            report.finished_at = datetime.now().isoformat()
            return report

        # ---- Step 2: Add to Cart & Go to Cart ----------------------------
        step = StepResult(name="cart_page")
        t0 = asyncio.get_event_loop().time()
        try:
            # Try common "Add to cart" selectors
            selectors = [
                'button:has-text("Add to cart")',
                'button:has-text("Add to Cart")',
                'button:has-text("Add To Cart")',
                'button[data-testid*="add-to-cart"]',
                'button[name="add-to-cart"]',
                'button[aria-label*="add to cart" i]',
                'input[value*="Add to Cart" i]',
                'button:has-text("Buy Now")',
                'button:has-text("Add to Bag")',
                'button:has-text("Add to basket")',
                # 中文 / 台灣電商常用
                'a:has-text("放入購物車")',
                'a:has-text("加入購物車")',
                'button:has-text("放入購物車")',
                'button:has-text("加入購物車")',
                'a:has-text("前往購買")',
                'a:has-text("立即購買")',
                'a:has-text("選購")',
                'input[value*="放入購物車" i]',
            ]
            added = False
            for sel in selectors:
                try:
                    await page.click(sel, timeout=STEP_TIMEOUT_MS)
                    added = True
                    break
                except Exception:
                    continue
            if not added:
                # Some SPA sites require scrolling; last-ditch JS click
                js_added = await page.evaluate(
                    """() => {
                        const btns = Array.from(document.querySelectorAll('button, a, input'));
                        // English patterns
                        let b = btns.find(b => /add\\s*to\\s*cart/i.test(b.textContent || b.value));
                        // Chinese patterns
                        if (!b) b = btns.find(b => /放入購物車|加入購物車|前往購買|立即購買|選購|加入購物/i.test(b.textContent || b.value));
                        // ID-based fallback for known Taiwan e-commerce sites
                        if (!b) b = document.getElementById('putinCart');
                        if (b) { b.click(); return true; }
                        return false;
                    }"""
                )
                if js_added:
                    added = True

            if not added:
                raise RuntimeError("Could not locate 'Add to cart' button")

            # Wait a beat for cart update / modal / redirect
            await asyncio.sleep(1)

            # If click already navigated to a cart-like page, we're done
            if any(k in page.url.lower() for k in ("cart", "basket", "bag")):
                cart_found = True
            else:
                # Navigate to cart — try common patterns
                from urllib.parse import urljoin
                cart_urls = ["/view_cart", "/cart", "/cart.html", "/basket", "/basket.html", "/shopping-cart", "/checkout/cart"]
                cart_found = False
                for cu in cart_urls:
                    try:
                        cart_url = urljoin(page.url, cu)
                        await page.goto(
                            cart_url,
                            wait_until="domcontentloaded",
                            timeout=STEP_TIMEOUT_MS,
                        )
                        cart_found = True
                        break
                    except Exception:
                        continue
                if not cart_found:
                    # Try clicking cart icon
                    cart_selectors = [
                        'a[href*="cart"]',
                        'a[href*="basket"]',
                        'button[aria-label*="cart" i]',
                        '[data-testid*="cart"]',
                    ]
                    for cs in cart_selectors:
                        try:
                            await page.click(cs, timeout=STEP_TIMEOUT_MS)
                            await asyncio.sleep(1)
                            cart_found = True
                            break
                        except Exception:
                            continue
            if not cart_found:
                raise RuntimeError("Could not navigate to cart page")

            step.url = page.url
            step.success = True
            step.notes = f"Title: {await page.title()}"
        except Exception as exc:
            step.success = False
            step.notes = f"Cart step failed: {exc}"
            anomalies.append(
                Anomaly(
                    step="cart_page",
                    severity="CRITICAL",
                    message="Could not reach cart page",
                    detail=str(exc),
                )
            )
        finally:
            step.duration_sec = asyncio.get_event_loop().time() - t0
            sp = _screenshot_path("cart_page", ts)
            await _save_screenshot(page, sp)
            step.screenshot_path = str(sp)
            step_results.append(step)

        if not step.success:
            await browser.close()
            report.steps = step_results
            report.anomalies = anomalies
            report.finished_at = datetime.now().isoformat()
            return report

        # ---- Step 3: Checkout --------------------------------------------
        step = StepResult(name="checkout_page")
        t0 = asyncio.get_event_loop().time()
        try:
            checkout_selectors = [
                'button:has-text("Checkout")',
                'button:has-text("Proceed to Checkout")',
                'a:has-text("Checkout")',
                'input[value*="Checkout" i]',
                'button:has-text("Continue")',
                'button[data-testid*="checkout"]',
            ]
            checked_out = False
            for sel in checkout_selectors:
                try:
                    await page.click(sel, timeout=STEP_TIMEOUT_MS)
                    checked_out = True
                    break
                except Exception:
                    continue
            if not checked_out:
                # SPA fallback
                checked_out = await page.evaluate(
                    """() => {
                        const btns = Array.from(document.querySelectorAll('button, a, input'));
                        const b = btns.find(b => /checkout|proceed/i.test(b.textContent || b.value));
                        if (b) { b.click(); return true; }
                        return false;
                    }"""
                )
                if checked_out:
                    checked_out = True  # JS returns True/False
            if not checked_out:
                raise RuntimeError("Could not initiate checkout")

            await asyncio.sleep(1)
            # Wait for navigation if any
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=STEP_TIMEOUT_MS)
            except Exception:
                pass

            # If still on cart-like page, try to proceed to payment/billing
            if any(k in page.url.lower() for k in ("cart", "basket", "bag")):
                proceed_selectors = [
                    'button:has-text("Continue")',
                    'button:has-text("Next")',
                    'button:has-text("Proceed")',
                    'a:has-text("Continue")',
                    'input[value*="Continue" i]',
                ]
                for sel in proceed_selectors:
                    try:
                        await page.click(sel, timeout=STEP_TIMEOUT_MS)
                        await asyncio.sleep(1)
                        await page.wait_for_load_state("domcontentloaded", timeout=STEP_TIMEOUT_MS)
                        break
                    except Exception:
                        continue

            step.url = page.url
            step.success = True
            step.notes = f"Title: {await page.title()}"
        except Exception as exc:
            step.success = False
            step.notes = f"Checkout step failed: {exc}"
            anomalies.append(
                Anomaly(
                    step="checkout_page",
                    severity="CRITICAL",
                    message="Could not reach checkout page",
                    detail=str(exc),
                )
            )
        finally:
            step.duration_sec = asyncio.get_event_loop().time() - t0
            sp = _screenshot_path("checkout_page", ts)
            await _save_screenshot(page, sp)
            step.screenshot_path = str(sp)
            step_results.append(step)

        if not step.success:
            await browser.close()
            report.steps = step_results
            report.anomalies = anomalies
            report.finished_at = datetime.now().isoformat()
            return report

        # ---- Step 4: Payment Page ----------------------------------------
        # We stop here — no real payment submission
        step = StepResult(name="payment_page")
        t0 = asyncio.get_event_loop().time()
        try:
            # If not clearly on a payment page yet, try to click "continue to payment"
            if not any(k in page.url.lower() for k in ("payment", "pay", "billing", "checkout/payment")):
                payment_selectors = [
                    'button:has-text("Continue to Payment")',
                    'button:has-text("Payment")',
                    'button:has-text("Continue")',
                    'a:has-text("Payment")',
                    'input[value*="Payment" i]',
                ]
                for sel in payment_selectors:
                    try:
                        await page.click(sel, timeout=STEP_TIMEOUT_MS)
                        await asyncio.sleep(1)
                        await page.wait_for_load_state("domcontentloaded", timeout=STEP_TIMEOUT_MS)
                        break
                    except Exception:
                        continue

            # Look for payment indicators (credit card fields, PayPal, etc.)
            payment_indicators = [
                'input[name*="card" i]',
                'input[placeholder*="card" i]',
                'input[name*="credit" i]',
                'input[name*="payment" i]',
                'iframe[src*="stripe" i]',
                'iframe[src*="paypal" i]',
                'button:has-text("Pay")',
                'button:has-text("Place Order")',
                'button:has-text("Complete Purchase")',
                'label:has-text("Credit Card")',
                'label:has-text("Payment")',
            ]
            found_payment = False
            for pi in payment_indicators:
                try:
                    await page.wait_for_selector(pi, timeout=STEP_TIMEOUT_MS)
                    found_payment = True
                    break
                except Exception:
                    continue

            if not found_payment:
                # Heuristic: page URL or title contains payment keywords
                url_title = f"{page.url} {await page.title()}".lower()
                if any(k in url_title for k in ("payment", "pay", "billing", "checkout")):
                    found_payment = True

            if found_payment:
                step.success = True
                step.notes = "Stopped before submitting payment (no real charge)"
            else:
                step.notes = "Payment indicators not found — may be a one-page checkout or different flow"
                step.success = True  # Not a failure, just unusual

            step.url = page.url
        except Exception as exc:
            step.success = False
            step.notes = f"Payment page step failed: {exc}"
            anomalies.append(
                Anomaly(
                    step="payment_page",
                    severity="WARNING",
                    message="Error inspecting payment page",
                    detail=str(exc),
                )
            )
        finally:
            step.duration_sec = asyncio.get_event_loop().time() - t0
            sp = _screenshot_path("payment_page", ts)
            await _save_screenshot(page, sp)
            step.screenshot_path = str(sp)
            step_results.append(step)

        # Anomaly scan on every step using final page state (Two-layer: Rule Engine → DeepSeek)
        for st in step_results:
            try:
                text = await page.content()
            except Exception:
                text = ""
            anomalies.extend(await _detect_anomalies_with_rule_engine(st.name, page, text, target_url))

        await browser.close()

    report.steps = step_results
    report.anomalies = anomalies
    report.finished_at = datetime.now().isoformat()
    return report


# ---------------------------------------------------------------------------
# Stagehand-enhanced path (optional — requires Browserbase API key)
# ---------------------------------------------------------------------------

async def _audit_with_stagehand(
    target_url: str, headless: bool
) -> AuditReport:
    if not _STAGEHAND_OK:
        raise RuntimeError("stagehand-py is not installed")

    api_key = os.getenv("BROWSERBASE_API_KEY")
    project_id = os.getenv("BROWSERBASE_PROJECT_ID")
    if not api_key or not project_id:
        raise RuntimeError(
            "Stagehand mode requires BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID"
        )

    report = AuditReport(
        target_url=target_url,
        started_at=datetime.now().isoformat(),
    )
    anomalies: list[Anomaly] = []
    step_results: list[StepResult] = []
    ts = _timestamp()

    config = StagehandConfig(
        env="BROWSERBASE",
        api_key=api_key,
        project_id=project_id,
        model_name="gpt-4o",
        verbose=1,
    )

    stage = Stagehand(
        config=config,
        server_url=STAGEHAND_SERVER_URL,
        model_api_key=os.getenv("MODEL_API_KEY"),
    )

    await stage.init()
    page: Page = stage.page  # StagehandPage wraps Playwright Page

    try:
        # Step 1 — Product Page
        step = StepResult(name="product_page")
        t0 = asyncio.get_event_loop().time()
        try:
            await page.goto(target_url, wait_until="networkidle")
            step.url = page.url
            step.success = True
            step.notes = f"Title: {await page.title()}"
        except Exception as exc:
            step.success = False
            step.notes = str(exc)
            anomalies.append(
                Anomaly(
                    step="product_page",
                    severity="CRITICAL",
                    message="Could not load product page",
                    detail=str(exc),
                )
            )
        finally:
            step.duration_sec = asyncio.get_event_loop().time() - t0
            sp = _screenshot_path("product_page", ts)
            await _save_screenshot(page, sp)
            step.screenshot_path = str(sp)
            step_results.append(step)

        if not step.success:
            return _finalize(report, step_results, anomalies)

        # Step 2 — Add to Cart & Cart Page (use Stagehand AI)
        step = StepResult(name="cart_page")
        t0 = asyncio.get_event_loop().time()
        try:
            await page.act("Click the 'Add to cart' button")
            await asyncio.sleep(2)
            await page.act("Navigate to the shopping cart / basket page")
            await asyncio.sleep(2)
            step.url = page.url
            step.success = True
            step.notes = f"Title: {await page.title()}"
        except Exception as exc:
            step.success = False
            step.notes = str(exc)
            anomalies.append(
                Anomaly(
                    step="cart_page",
                    severity="CRITICAL",
                    message="Could not reach cart page",
                    detail=str(exc),
                )
            )
        finally:
            step.duration_sec = asyncio.get_event_loop().time() - t0
            sp = _screenshot_path("cart_page", ts)
            await _save_screenshot(page, sp)
            step.screenshot_path = str(sp)
            step_results.append(step)

        if not step.success:
            return _finalize(report, step_results, anomalies)

        # Step 3 — Checkout
        step = StepResult(name="checkout_page")
        t0 = asyncio.get_event_loop().time()
        try:
            await page.act("Proceed to checkout")
            await asyncio.sleep(2)
            step.url = page.url
            step.success = True
            step.notes = f"Title: {await page.title()}"
        except Exception as exc:
            step.success = False
            step.notes = str(exc)
            anomalies.append(
                Anomaly(
                    step="checkout_page",
                    severity="CRITICAL",
                    message="Could not reach checkout page",
                    detail=str(exc),
                )
            )
        finally:
            step.duration_sec = asyncio.get_event_loop().time() - t0
            sp = _screenshot_path("checkout_page", ts)
            await _save_screenshot(page, sp)
            step.screenshot_path = str(sp)
            step_results.append(step)

        if not step.success:
            return _finalize(report, step_results, anomalies)

        # Step 4 — Payment Page (stop before submitting)
        step = StepResult(name="payment_page")
        t0 = asyncio.get_event_loop().time()
        try:
            # Extract whether we're on a payment page
            result = await page.extract(
                instruction="Is this a payment / billing page? Answer YES or NO."
            )
            is_payment = "yes" in (result.text or "").lower()
            if is_payment:
                step.success = True
                step.notes = "Stopped before submitting payment (no real charge)"
            else:
                step.notes = "Payment page not clearly identified — stopping here"
                step.success = True
            step.url = page.url
        except Exception as exc:
            step.success = False
            step.notes = str(exc)
            anomalies.append(
                Anomaly(
                    step="payment_page",
                    severity="WARNING",
                    message="Error inspecting payment page",
                    detail=str(exc),
                )
            )
        finally:
            step.duration_sec = asyncio.get_event_loop().time() - t0
            sp = _screenshot_path("payment_page", ts)
            await _save_screenshot(page, sp)
            step.screenshot_path = str(sp)
            step_results.append(step)

        # Anomaly scan (Two-layer: Rule Engine → DeepSeek)
        for st in step_results:
            try:
                text = await page.content()
            except Exception:
                text = ""
            anomalies.extend(await _detect_anomalies_with_rule_engine(st.name, page, text, target_url))

    finally:
        await stage.close()

    return _finalize(report, step_results, anomalies)


def _finalize(
    report: AuditReport, steps: list[StepResult], anomalies: list[Anomaly]
) -> AuditReport:
    report.steps = steps
    report.anomalies = anomalies
    report.finished_at = datetime.now().isoformat()
    return report


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

async def main() -> int:
    parser = argparse.ArgumentParser(
        description="CartRescue AI — Checkout Auditor"
    )
    parser.add_argument("url", help="Product page URL to audit")
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_HEADLESS,
        help="Run browser headless (default: True)",
    )
    parser.add_argument(
        "--stagehand",
        action="store_true",
        help="Use Stagehand AI mode (requires BROWSERBASE_API_KEY)",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=REPORT_DIR,
        help="Directory to save text report",
    )
    parser.add_argument(
        "--screenshot-dir",
        type=Path,
        default=SCREENSHOT_DIR,
        help="Directory to save screenshots",
    )
    args = parser.parse_args()

    import sys
    _mod = sys.modules[__name__]
    _mod.SCREENSHOT_DIR = args.screenshot_dir
    _mod.REPORT_DIR = args.report_dir
    _ensure_dirs()

    target = _normalize_url(args.url)
    print(f"[CartRescue Auditor] Starting audit for {target}", flush=True)

    use_stagehand = args.stagehand
    if use_stagehand and not _STAGEHAND_OK:
        print(
            "[WARN] Stagehand requested but not installed; falling back to Playwright",
            flush=True,
        )
        use_stagehand = False

    if use_stagehand and (
        not os.getenv("BROWSERBASE_API_KEY")
        or not os.getenv("BROWSERBASE_PROJECT_ID")
    ):
        print(
            "[WARN] Stagehand requested but API keys missing; falling back to Playwright",
            flush=True,
        )
        use_stagehand = False

    try:
        if use_stagehand:
            report = await _audit_with_stagehand(target, args.headless)
        else:
            report = await _audit_with_playwright(target, args.headless)
    except Exception as exc:
        traceback.print_exc()
        print(f"[FATAL] Audit failed: {exc}", file=sys.stderr, flush=True)
        return 2

    # Compute total duration
    if report.steps:
        report.total_duration_sec = sum(s.duration_sec for s in report.steps)

    text = report.to_text()
    print(text, flush=True)

    # Write report file
    rp = _report_path(_timestamp())
    rp.write_text(text, encoding="utf-8")
    print(f"\n[CartRescue Auditor] Report saved to {rp}", flush=True)
    print(
        f"[CartRescue Auditor] Screenshots saved to {SCREENSHOT_DIR}",
        flush=True,
    )

    return 1 if report.anomalies else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
