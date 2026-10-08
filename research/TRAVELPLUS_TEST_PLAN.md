# CartRescue AI 模型實測計畫 — TravelPlus 網站測試

## 測試目標網站
**https://www.travelplus.com.tw/**

## 測試目的
用真實電商網站驗證不同 AI 模型在瀏覽器自動化結帳審計的表現，找出最適合 CartRescue 的模型組合。

## 測試模型清單（20+）

### 第一梯隊（導航模型）
1. Gemini 2.0 Flash
2. Gemini 2.0 Flash-Lite
3. Gemini 3.1 Flash
4. GPT-4o-mini
5. DeepSeek V4.1 Flash
6. Kimi K2.6

### 第二梯隊（異常判讀模型）
7. Claude Sonnet 5 (Intro)
8. Claude Opus 4.8
9. Claude 3.5 Sonnet
10. Gemini 2.0 Pro
11. Gemini 3.1 Pro
12. GPT-4o
13. GPT-5.5
14. Kimi K3

### 第三梯隊（備援/新模型）
15. Qwen2.5-VL-72B
16. Grok 4.1
17. MiniMax M3
18. Llama 3.1 405B

## 測試項目

### 項目 1：頁面導航能力
- 從首頁進入商品頁
- 加入購物車
- 進入結帳頁
- 填寫基本資訊
- 到達付款頁（停止）
- 記錄：成功率、步驟數、時間、錯誤類型

### 項目 2：異常檢測能力
- 截圖分析：頁面是否正確載入
- 錯誤訊息識別：404、500、JavaScript 錯誤
- 流程阻斷識別：按鈕無法點擊、表單無法提交
- 記錄：準確率、誤報率、漏報率

### 項目 3：折扣碼驗證能力
- 輸入測試折扣碼
- 判斷折扣碼是否有效
- 識別錯誤訊息（如「折扣碼無效」、「已過期」）
- 記錄：成功率、辨識準確度

### 項目 4：成本與延遲
- 每次 API 呼叫的 token 消耗
- 每次 API 呼叫的費用
- 每次 API 呼叫的延遲（TTFT + 總時間）
- 記錄：單次審計總成本、總時間

## 文獻研究

### 搜尋目標
1. **arxiv.org**: "browser automation" "web agent" "GUI testing" "checkout flow testing"
2. **arxiv.org**: "multimodal LLM" "vision language model" "computer use"
3. **Google Scholar**: 電商棄單率、結帳流程優化、自動化測試
4. **產業報告**: Baymard Institute、SimplyCodes、Noibu 技術白皮書
5. **論壇/部落格**: Stagehand evals、Browser Use benchmarks、Skyvern comparisons

### 每日進度回報格式
- 當日測試了哪些模型
- 測試結果摘要（成功率、成本、時間）
- 發現的問題或驚喜
- 明日計畫

## 終止條件
1. 所有 18 個模型完成至少一次完整測試
2. 產出每個模型的詳細測試報告（成功率、成本、延遲、優缺點）
3. 產出最終模型排名與推薦組合
4. 完成文獻綜述（至少 10 篇相關論文/文章）
5. 所有結果儲存並確認可讀

## 輸出檔案
- `/home/cartrescue/CartRescue_AI/research/TRAVELPLUS_MODEL_TEST_DAY1.md`
- `/home/cartrescue/CartRescue_AI/research/TRAVELPLUS_MODEL_TEST_DAY2.md`
- ...（每日報告）
- `/home/cartrescue/CartRescue_AI/research/TRAVELPLUS_MODEL_TEST_FINAL.md`（最終總結）
- `/home/cartrescue/CartRescue_AI/research/LITERATURE_REVIEW_BROWSER_AGENTS.md`（文獻綜述）

---

*計畫建立日期：2026-09-17*
*負責：Scout（斯考特）*
