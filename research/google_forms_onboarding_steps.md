# Google Forms 上架步驟說明

## 前置需求

- Google 帳號（建議使用公司帳號 cartrescue.ai 域名）
- 問卷內容已審核定稿
- 問卷連結（發布後產生）

---

## Step 1：建立空白表單

1. 登入 [Google Forms](https://forms.google.com)。
2. 點選「+ 空白」建立新表單。
3. 表單標題輸入：`CartRescue AI 市場調查問卷`
4. 描述欄貼上：
   ```
   發放對象：SHOPLINE / Shopify / 91APP 台灣店家之電商負責人、營運或行銷主管
   目標數量：50 份有效問卷
   填答完成者將優先獲得「免費結帳健檢」資格！
   如有問題請聯繫：vincent@cartrescue.ai / LINE: @cartrescue
   ```

---

## Step 2：分頁與題目設定

建議將問卷分為 7 個分頁（Sections），對應原問卷 A–G 區塊：

| 分頁名稱 | 題目數 | 備註 |
|---------|-------|------|
| A. 篩選與受訪者輪廓 | 4 | 必填，作為篩選條件 |
| B. 結帳故障痛點驗證 | 4 | B1 設定「不確定」跳題至 B3 |
| C. 優惠券營運痛點驗證 | 6 | C3「否」跳至 C5；C4「不知道有沒有」跳至 C6 |
| D. 現有替代方案 | 2 | 可複選 |
| E. 付費意願（Van Westendorp） | 5 | 開放題建議設「簡短答案」並提示單位 |
| F. Beta 合作意願 | 7 | F1 選「願意」再顯示聯絡欄位（使用條件邏輯） |
| G. 其他建議 | 3 | 全選填 |

### 條件邏輯設定（關鍵跳題）

- **B1 → B3**：若選「不確定」，跳過 B2，直接到 B3。
- **C3 → C5**：若選「否」，跳過 C4，直接到 C5。
- **C4 → C6**：若選「不知道有沒有」，跳過 C4-2，直接到 C6。
- **F1 → 顯示聯絡欄位**：若選「願意」，顯示 F2 所有欄位；若選「暫時不需要」，隱藏 F2。

---

## Step 3：題型與驗證設定

- **單選題**：使用「選擇題」（Multiple choice）
- **多選題**：使用「核取方塊」（Checkbox）
- **開放題**：使用「簡短答案」（Short answer），E1–E4 建議加上「數字驗證」或「正規表示式」限制為純數字
- **其他選項**：單選與多選題的最後一個選項可勾選「其他」讓受訪者自行填寫
- **必填題**：A 區塊全設必填；B、C、E 區塊核心題設必填；其餘選填

---

## Step 4：表單外觀設定

1. 點選右上角「自訂主題」（調色盤圖示）。
2. 建議配色：
   - 標題文字：`#1A1A2E`（深藍黑）
   - 背景顏色：`#F5F7FA`（淺灰白）
   - 強調色：`#E94560`（品牌紅）
3. 上傳品牌 Logo（如有）。
4. 字型建議：標題「Noto Sans TC」、內文「Noto Sans TC」。

---

## Step 5：回應收集設定

1. 點選「回應」分頁 → 確認「接受回應」已開啟。
2. 建議設定：
   - ✅ 收集電子郵件地址（如需追蹤 Beta 名單）
   - ❌ 限制為 1 回應（視需求決定，初期建議不限制，避免擋到同一公司多人填寫）
   - ✅ 回應複製到試算表（方便即時分析）
3. 點選「建立試算表」→ 選擇「建立新試算表」，命名為 `CartRescue_Survey_Responses`。

---

## Step 6：發布與分享

1. 點選右上角「傳送」。
2. 分享方式：
   - **連結**：點選「連結」圖示 → 縮短網址 → 複製短網址（如 `https://forms.gle/XXXXXX`）
   - **嵌入**：如需放到網站，可複製 HTML iframe 程式碼
   - **Email**：可直接寄送給已知名單
3. 將短網址貼回 `survey_promotion_post.md` 的 `[問卷連結將於 Google Forms 上架後補上]` 處。

---

## Step 7：測試與上線檢查清單

- [ ] 使用「預覽」模式，以受訪者視角完整填寫一次
- [ ] 測試所有條件邏輯（跳題）是否正確
- [ ] 確認「其他」選項可正常輸入文字
- [ ] 確認 Beta 聯絡欄位在選「願意」後才顯示
- [ ] 確認回應有正確寫入試算表
- [ ] 檢查手機版顯示是否正常
- [ ] 發布前請 Vincent 做最後審閱

---

## 問卷發布時程建議

| 時間 | 動作 |
|------|------|
| D-1 | Google Forms 上架完成、連結測試、試算表連結確認 |
| D-Day | 於「台灣電商創業家」社團發布貼文 |
| D+1 | 追蹤回應數、回覆前 10 則留言互動 |
| D+3 | 若回應未達 30 份，於 SHOPLINE / Shopify 商家社群二次發布 |
| D+7 | 統計回應數，確認是否達標 50 份；進行初步資料清理 |
| D+14 | 關閉表單或視情況延長；彙整 Van Westendorp 價格帶分析 |

---

## 相關檔案

- 問卷內容原始檔：`/home/cartrescue/CartRescue_AI/research/CUSTOMER_SURVEY.md`
- Google Forms JSON 結構檔：`/home/cartrescue/CartRescue_AI/research/survey_googleforms_ready.json`
- 社群貼文草稿：`/home/cartrescue/CartRescue_AI/research/survey_promotion_post.md`
- 本上架說明檔：`/home/cartrescue/CartRescue_AI/research/google_forms_onboarding_steps.md`
