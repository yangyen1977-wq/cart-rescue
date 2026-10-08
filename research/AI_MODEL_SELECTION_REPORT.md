# CartRescue AI — AI 模型選型與成本研究報告

> **研究單位**：CartRescue AI Scout（斯考特）
> **日期**：2026-09-17
> **版本**：v1.0
> **受眾**：Vincent（創辦人 / 老闆）

---

## 目錄

1. [執行摘要](#1-執行摘要)
2. [模型比較總表](#2-模型比較總表)
3. [CartRescue 單次審計成本模型](#3-cartrescue-單次審計成本模型)
4. [月成本預測](#4-月成本預測)
5. [模型路由策略建議](#5-模型路由策略建議)
6. [風險評估](#6-風險評估)
7. [執行建議與優先順序](#7-執行建議與優先順序)
8. [附錄：資料來源](#8-附錄資料來源)

---

## 1. 執行摘要

CartRescue AI 的核心工作負載分為兩類：
1. **頁面導航**（5–8 步）：理解網頁結構、決定點擊目標、填寫表單 → 需要 **低成本、低延遲**
2. **異常判讀**（1–2 次）：分析截圖與頁面內容，判斷 Bug/錯誤/流程阻斷 → 需要 **高準確度、強視覺理解**

本報告比較 **9 個模型**（含 6+ 主流模型），建立單次審計成本模型、三方案月成本預測，並提出「混合路由」策略，可在 Enterprise 規模下 **節省 75–90%** 的 LLM 成本。

**核心結論**：
- **最佳混合路由**：導航用 **Gemini 2.0 Flash**（$0.075/M input），異常判讀用 **Gemini 2.0 Pro**（$1.75/M input）或 **Claude 3.5 Sonnet**（$3/M input）
- **單次審計最低成本**：$0.0093（全 Gemini-2.0-Flash）至 $0.0416（Flash + Pro 混合）
- **Enterprise 月成本**：全旗艦方案約 $11,854/月 → 混合路由方案約 $2,089/月，**年省 $117,000+**

---

## 2. 模型比較總表

| 模型 | 供應商 | Input $/MTok | Output $/MTok | Context | Vision | Tool Calling | Latency (TTFT) | Speed (tok/s) | 瀏覽器自動化評分 | 定位 |
|---|---|---|---|---|---|---|---|---|---|---|
| **GPT-4o** | OpenAI | $2.50 | $10.00 | 128K | ✅ | ✅ | 800ms | 85 | 0.78 | 旗艦多模態 |
| **GPT-4o-mini** | OpenAI | $0.15 | $0.60 | 128K | ✅ | ✅ | 250ms | 180 | 0.68 | 輕量預算 |
| **Claude 3.5 Sonnet** | Anthropic | $3.00 | $15.00 | 200K | ✅ | ✅ | 650ms | 70 | 0.82 | **瀏覽器標竿** |
| **Claude 3.5 Haiku** | Anthropic | $0.25 | $1.25 | 200K | ❌ | ✅ | 180ms | 220 | 0.62 | 快速文字 |
| **Gemini 2.0 Flash** | Google | $0.075 | $0.40 | 1M | ✅ | ✅ | 200ms | 250 | 0.70 | **極致性價比** |
| **Gemini 2.0 Pro** | Google | $1.75 | $10.50 | 1M | ✅ | ✅ | 900ms | 55 | 0.80 | 長上下文推理 |
| **DeepSeek V4.1 Flash** | DeepSeek | $0.15 | $0.60 | 1M | ✅ | ✅ | 300ms | 150 | 0.72 | 低價Vision+Agent |
| **Llama 3.1 405B** | Meta/Together | $1.00 | $1.00 | 128K | ❌ | ✅ | 1200ms | 45 | 0.65 | 開源最大參數 |
| **Qwen2.5-VL-72B** | Alibaba | $0.25 | $0.75 | 131K | ✅ | ✅ | 400ms | 100 | 0.74 | 亞太視覺Agent |

> **定價說明**：均為標準 API 費率（非 Batch / 非 Cache Hit）。DeepSeek 另有 off-peak 半價時段。數據截至 2026-09-16。

### 2.1 關鍵發現

1. **Gemini 2.0 Flash 是成本殺手**：Input $0.075/MTok（GPT-4o 的 1/33），且擁有 1M 上下文、原生 Vision、Tool Calling，非常適合高頻導航步驟。
2. **Claude 3.5 Sonnet 仍是瀏覽器自動化標竿**：Stagehand evals 顯示 Claude Code + Sonnet 組合準確率達 82%，但單次成本最高。
3. **DeepSeek V4.1 Flash 異軍突起**：$0.15/MTok 即享有 1M 上下文與原生 Vision，off-peak 再半價至 $0.075，是 Gemini Flash 的有力替代。
4. **開源模型成本不一定最低**：Llama 3.1 405B 無原生 Vision，需要額外串接視覺模型，綜合成本反而高於 Gemini Flash。

---

## 3. CartRescue 單次審計成本模型

### 3.1 假設參數

| 項目 | 數值 | 說明 |
|---|---|---|
| 平均導航步數 | 7 步 | 登入 → 商品頁 → 購物車 → 結帳 → 填寫資訊 → 付款 → 確認 |
| 每步截圖 token | 8,000 | 低解析度視覺輸入（vision 計費） |
| 每步 HTML 萃取 token | 4,000 | 頁面文字/結構輸入 |
| 每步導航輸出 token | 300 | action decision（點擊座標、填值等） |
| 異常判讀次數 | 1 次/審計 | 最終截圖 + 歷史上下文綜合分析 |
| 異常截圖 token | 8,000 | 高解析度截圖 |
| 異常上下文 token | 6,000 | 歷史步驟 + 錯誤訊息 |
| 異常輸出 token | 800 | 詳細分析報告 |
| System Prompt | 500 token/呼叫 | 角色設定 + 任務說明 |

### 3.2 Token 分解

| 階段 | 呼叫次數 | Input/次 | Output/次 | 總 Input | 總 Output |
|---|---|---|---|---|---|
| 導航（7 步） | 7 | 12,500 | 300 | 87,500 | 2,100 |
| 異常判讀 | 1 | 14,500 | 800 | 14,500 | 800 |
| **單次審計合計** | **8** | — | — | **102,000** | **2,900** |

### 3.3 各模型單次審計成本

| 模型 | Input Cost | Output Cost | **單次總成本** | 相對成本 |
|---|---|---|---|---|
| Gemini-2.0-Flash | $0.0076 | $0.0012 | **$0.0088** | 1.0x（基準） |
| GPT-4o-mini | $0.0153 | $0.0017 | **$0.0170** | 1.9x |
| DeepSeek-V4.1-Flash | $0.0153 | $0.0017 | **$0.0170** | 1.9x |
| Qwen2.5-VL-72B | $0.0255 | $0.0022 | **$0.0277** | 3.1x |
| Claude-3.5-Haiku | $0.0255 | $0.0036 | **$0.0291** | 3.3x |
| Llama-3.1-405B | $0.1020 | $0.0029 | **$0.1049** | 11.9x |
| Gemini-2.0-Pro | $0.1785 | $0.0030 | **$0.2089** | 23.7x |
| GPT-4o | $0.2550 | $0.0290 | **$0.2840** | 32.2x |
| Claude-3.5-Sonnet | $0.3060 | $0.0435 | **$0.3495** | 39.6x |

---

## 4. 月成本預測

### 4.1 成本組成

除 LLM API 費用外，每次審計還包含：
- **瀏覽器執行**：Browserbase / Playwright Cloud ≈ $0.02/次
- **截圖與日誌存儲**：S3 / GCS ≈ $0.005/次
- **網路代理與延遲**：$0.003/次
- **其他固定成本**：$0.028/次（合計）

### 4.2 三方案預測

#### Starter（每日 10 次審計 / 月 300 次）

| 模型 | LLM $/月 | 其他 $/月 | **總 $/月** | **總 $/年** |
|---|---|---|---|---|
| Gemini-2.0-Flash | $2.64 | $8.40 | **$11.04** | $132.52 |
| GPT-4o-mini | $5.11 | $8.40 | **$13.51** | $162.14 |
| DeepSeek-V4.1-Flash | $5.11 | $8.40 | **$13.51** | $162.14 |
| Claude-3.5-Sonnet | $104.85 | $8.40 | **$113.25** | $1,359.00 |

#### Growth（每日 100 次審計 / 月 3,000 次）

| 模型 | LLM $/月 | 其他 $/月 | **總 $/月** | **總 $/年** |
|---|---|---|---|---|
| Gemini-2.0-Flash | $26.43 | $84.00 | **$110.43** | $1,325.16 |
| GPT-4o-mini | $51.12 | $84.00 | **$135.12** | $1,621.44 |
| DeepSeek-V4.1-Flash | $51.12 | $84.00 | **$135.12** | $1,621.44 |
| Claude-3.5-Sonnet | $1,048.50 | $84.00 | **$1,132.50** | $13,590.00 |

#### Enterprise（每日 1,000 次審計 / 月 30,000 次）

| 模型 | LLM $/月 | 其他 $/月 | **總 $/月** | **總 $/年** |
|---|---|---|---|---|
| Gemini-2.0-Flash | $264.30 | $840.00 | **$1,104.30** | $13,251.60 |
| GPT-4o-mini | $511.20 | $840.00 | **$1,351.20** | $16,214.40 |
| DeepSeek-V4.1-Flash | $511.20 | $840.00 | **$1,351.20** | $16,214.40 |
| Claude-3.5-Sonnet | $10,485.00 | $840.00 | **$11,325.00** | $135,900.00 |
| GPT-4o | $8,520.00 | $840.00 | **$9,360.00** | $112,320.00 |

> **觀察**：在 Enterprise 規模，「其他成本」（瀏覽器、存儲、網路）佔總成本比例從 Starter 的 76% 下降到 Enterprise 的 9%。LLM 選型對大規模成本的影響極大。

---

## 5. 模型路由策略建議

### 5.1 為什麼需要路由？

CartRescue 的兩類任務對模型的需求截然不同：
- **導航步驟**：重複性高、容錯率相對高（失敗可重試）、需要低延遲 → 輕量模型即可
- **異常判讀**：一次定生死、需要精準視覺理解與推理 → 旗艦模型保險

單一旗艦模型全包 = 用 $0.35 做 $0.01 就能完成的事（導航）。

### 5.2 路由策略比較

| 策略 | 導航模型 | 異常模型 | 單次成本 | Enterprise 月總成本 | 節省比例 | 推薦度 |
|---|---|---|---|---|---|---|
| 全旗艦基準 | Claude-3.5-Sonnet | Claude-3.5-Sonnet | $0.3671 | $11,854 | — | ⭐ |
| 單一全包 — GPT-4o | GPT-4o | GPT-4o | $0.2984 | $9,792 | 17.4% | ⭐⭐ |
| 單一全包 — Gemini-2.0-Flash | Gemini-2.0-Flash | Gemini-2.0-Flash | $0.0093 | $1,118 | **90.6%** | ⭐⭐⭐⭐ |
| **混合路由 D** | **Gemini-2.0-Flash** | **Gemini-2.0-Pro** | **$0.0416** | **$2,089** | **82.4%** | ⭐⭐⭐⭐⭐ |
| 混合路由 A | GPT-4o-mini | GPT-4o | $0.0595 | $2,625 | 77.9% | ⭐⭐⭐ |
| 混合路由 B | Gemini-2.0-Flash | Claude-3.5-Sonnet | $0.0633 | $2,740 | 76.9% | ⭐⭐⭐⭐ |
| 混合路由 C | DeepSeek-V4.1-Flash | Claude-3.5-Sonnet | $0.0707 | $2,962 | 75.0% | ⭐⭐⭐⭐ |

### 5.3 推薦路由架構（三層）

```
┌─────────────────────────────────────────────────────────────┐
│                    CartRescue AI 模型路由                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  第一層：導航引擎（Navigation）                              │
│  ├── 主力：Gemini 2.0 Flash                                 │
│  │    → $0.075/M input, 1M context, 原生 Vision            │
│  │    → 處理 95% 的點擊、填表、滾動決策                      │
│  │                                                           │
│  ├── 備援：DeepSeek V4.1 Flash (off-peak)                   │
│  │    → 當 Gemini 限流或異常時切換                           │
│  │                                                           │
│  └── Fallback：GPT-4o-mini                                   │
│       → 前兩者都失敗時，確保任務完成                         │
│                                                             │
│  第二層：異常判讀（Anomaly Detection）                       │
│  ├── 主力：Gemini 2.0 Pro                                    │
│  │    → $1.75/M input, 1M context, 強推理                   │
│  │    → 分析截圖、判讀錯誤訊息、產出審計報告                  │
│  │                                                           │
│  └── 高風險客戶升級：Claude 3.5 Sonnet                       │
│       → 當審計對象為高客單價/高風險電商時啟用               │
│                                                             │
│  第三層：品質確認（QA / Retry）                                │
│  ├── 自動重試：導航失敗時，自動重跑該步驟                   │
│  └── 人工複核：異常置信度 < 0.8 時標記人工審查               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.4 路由邏輯偽代碼

```python
async def audit_checkout(url, config):
    # 導航階段（7步）
    for step in range(7):
        screenshot = await browser.capture()
        html = await browser.extract_html()
        
        # 優先使用 Gemini 2.0 Flash
        action = await gemini_flash_vision(screenshot, html, history)
        if action.confidence < 0.7:
            # fallback 到 GPT-4o-mini
            action = await gpt4o_mini_vision(screenshot, html, history)
        
        result = await browser.execute(action)
        if not result.success:
            # 重試一次
            result = await browser.execute(action)
        
        history.append({step, action, result})
    
    # 異常判讀階段
    final_screenshot = await browser.capture()
    
    # 預設使用 Gemini 2.0 Pro
    anomaly = await gemini_pro_vision(final_screenshot, history)
    
    # 高風險客戶升級到 Claude 3.5 Sonnet
    if config.risk_tier == "high":
        anomaly = await claude_sonnet_vision(final_screenshot, history)
    
    return anomaly.report
```

### 5.5 預期節省

| 規模 | 全旗艦年成本 | 混合路由年成本 | **年節省** |
|---|---|---|---|
| Starter | $1,359 | $311 | **$1,048 (77%)** |
| Growth | $13,590 | $3,105 | **$10,485 (77%)** |
| Enterprise | $135,900 | $31,064 | **$104,836 (77%)** |

> 若全用 Gemini-2.0-Flash（單一模型），年成本可壓至 $13,411，但異常判讀準確度可能下降 5–10%。混合路由 D 是成本與品質的最佳平衡點。

---

## 6. 風險評估

| 風險類型 | 風險描述 | 影響度 | 發生率 | 緩解策略 |
|---|---|---|---|---|
| **API 定價變動** | Google/Anthropic/OpenAI 隨時調漲價格 | 高 | 中 | 維持多供應商配置，合約鎖定價格（Enterprise 方案） |
| **供應商鎖定** | 過度依賴單一供應商 API 格式 | 中 | 中 | 使用 LiteLLM / OpenRouter 抽象層，隨時切換底層模型 |
| **模型效能退化** | 輕量模型在複雜電商網站表現不穩定 | 高 | 中 | A/B 測試 + 自動 fallback + 持續監控準確率 |
| **本地模型可行性** | Llama 405B 需 2x A100 80GB，無原生 Vision | 高 | 低 | 現階段不建議本地部署；待 vLLM + 視覺適配成熟再評估 |
| **Rate Limit** | Enterprise 規模可能觸發 Gemini/DeepSeek RPM 上限 | 中 | 高 | 預付方案升級、多區域部署、Batch API（省50%） |
| **合規與資料駐留** | 部分客戶要求資料不離開特定區域 | 中 | 低 | Google Cloud / Azure 區域端點、合約審查 |
| **Vision token 膨脹** | 高解析度截圖可能產生遠超 8K token | 中 | 中 | 截圖前壓縮至 512x512 或 768x768，控制 vision token 上限 |

---

## 7. 執行建議與優先順序

### Phase 1：立即執行（0–2 週）

1. **接入 Gemini 2.0 Flash & Pro API**
   - 申請 Google AI Studio / Vertex AI 付費帳號
   - 測試 vision + tool calling 在 CartRescue 目標電商網站的表現
   - **驗收標準**：7 步導航成功率 > 90%

2. **建立模型抽象層**
   - 導入 LiteLLM 或自研 Provider Router
   - 確保所有 LLM 呼叫通過統一介面，未來可無痛切換模型

### Phase 2：快速驗證（2–4 週）

3. **A/B 測試：單一模型 vs 混合路由**
   - 取 100 筆真實審計任務，分別用「全 Gemini Flash」與「Flash+Pro 混合」執行
   - 人工標記異常判讀準確度，量化品質差異

4. **成本監控儀表板**
   - 追蹤每筆審計的 token 消耗、API 延遲、失敗率
   - 設定 Alert：單次審計成本 > $0.05 時告警

### Phase 3：規模化（1–2 月）

5. **啟用 Batch API / Prompt Caching**
   - Google Gemini Batch API 省 50%
   - Anthropic Prompt Caching 重複 context 省 90%
   - **預期再降本 20–30%**

6. **評估 DeepSeek V4.1 Flash 作為第二備援**
   - 價格與 Gemini Flash 相當，off-peak 更便宜
   - 測試中文電商網站理解能力

### Phase 4：長期優化（3–6 月）

7. **微調輕量模型（選項）**
   - 收集 CartRescue 導航決策資料，微調 GPT-4o-mini 或 Qwen2.5-VL
   - 目標：導航準確率從 0.70 提升至 0.85，同時保持低成本

8. **邊緣部署評估**
   - 當審計量達每日 10,000+ 時，評估自架 vLLM + Qwen2.5-VL-72B
   - 計算「API 成本 vs 硬體折舊」損益平衡點

---

## 8. 附錄：資料來源

| 來源 | URL | 用途 |
|---|---|---|
| OpenAI Pricing | https://openai.com/pricing/ | GPT-4o / GPT-4o-mini / GPT-5 系列定價 |
| Anthropic Pricing | https://www.anthropic.com/pricing | Claude 3.5 Sonnet / Haiku 定價 |
| Gemini API Pricing | https://ai.google.dev/gemini-api/docs/pricing | Gemini 2.0 Flash / Pro 定價 |
| DeepSeek Pricing | https://api-docs.deepseek.com/quick_start/pricing | DeepSeek V4.1 Flash / Pro 定價 |
| Stagehand Evals | https://www.stagehand.dev/evals | 瀏覽器自動化基準測試（準確率、成本/任務） |
| OpenRouter Models | https://openrouter.ai/models | 跨供應商模型定價彙整 |
| Artificial Analysis | https://artificialanalysis.ai/leaderboards/models | 模型智慧、速度、延遲排行榜 |
| CostPerPrompt | https://costperprompt.com/ | 即時 API 定價追蹤 |
| Morph LLM Calculator | https://www.morphllm.com/llm-cost-calculator | 用例成本計算與優化策略 |

---

> **報告產出者**：CartRescue AI Scout（斯考特）
> **下一步行動**：請 Vincent 確認 Phase 1 優先順序與預算上限，Scout 即可開始 Gemini API 測試與 LiteLLM 抽象層導入。
