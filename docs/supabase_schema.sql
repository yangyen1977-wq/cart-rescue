-- ═══════════════════════════════════════════════════════
-- CartRescue AI — Supabase 異常資料表建表腳本
-- 執行方式：在 Supabase SQL Editor 中貼上並執行
-- ═══════════════════════════════════════════════════════

-- 啟用 Row Level Security（RLS）與 UUID 擴充
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── 主資料表：anomalies ──────────────────────────────
CREATE TABLE IF NOT EXISTS anomalies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anomaly_detected BOOLEAN NOT NULL DEFAULT TRUE,
    type            TEXT NOT NULL,
    severity        TEXT NOT NULL CHECK (severity IN ('critical', 'warning', 'info')),
    confidence      INTEGER NOT NULL CHECK (confidence BETWEEN 0 AND 100),
    description     TEXT NOT NULL,
    suggested_fix   TEXT,
    rule_id         TEXT NOT NULL,
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    evidence        JSONB DEFAULT '{}',
    alerted         BOOLEAN DEFAULT FALSE,      -- 是否已發送 LINE 推播
    alert_sent_at   TIMESTAMPTZ               -- 推播發送時間
);

-- ── 索引設計（加速查詢）────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_anomalies_severity ON anomalies(severity);
CREATE INDEX IF NOT EXISTS idx_anomalies_type ON anomalies(type);
CREATE INDEX IF NOT EXISTS idx_anomalies_detected_at ON anomalies(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_anomalies_created_at ON anomalies(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_anomalies_alerted ON anomalies(alerted) WHERE alerted = FALSE;
CREATE INDEX IF NOT EXISTS idx_anomalies_rule_id ON anomalies(rule_id);

-- ── Row Level Security 策略 ────────────────────────────
ALTER TABLE anomalies ENABLE ROW LEVEL SECURITY;

-- 允許 service_role 完整存取（後端寫入用）
CREATE POLICY "Service role full access" ON anomalies
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 允許 authenticated 使用者唯讀自己的資料（如未來開放前端查詢）
-- CREATE POLICY "Users can read own anomalies" ON anomalies
--     FOR SELECT
--     TO authenticated
--     USING (auth.uid() = user_id);

-- ── 彙整推播輔助視圖（每小時 Warning 統計）─────────────
CREATE OR REPLACE VIEW warning_summary_last_hour AS
SELECT
    type,
    COUNT(*) AS count,
    MAX(confidence) AS max_confidence,
    MAX(detected_at) AS last_detected_at
FROM anomalies
WHERE severity = 'warning'
  AND detected_at > NOW() - INTERVAL '1 hour'
GROUP BY type
ORDER BY count DESC;

-- ── 觸發函式：自動更新 alerted 時間戳 ──────────────────
CREATE OR REPLACE FUNCTION update_alert_sent_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.alerted = TRUE AND OLD.alerted = FALSE THEN
        NEW.alert_sent_at := NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_anomalies_alert_sent
    BEFORE UPDATE ON anomalies
    FOR EACH ROW
    EXECUTE FUNCTION update_alert_sent_at();

-- ── 註解說明 ─────────────────────────────────────────
COMMENT ON TABLE anomalies IS 'CartRescue AI 異常檢測結果主表，與 rule_engine.py 輸出格式一致';
COMMENT ON COLUMN anomalies.type IS '異常類型，對應 AnomalyType Enum';
COMMENT ON COLUMN anomalies.severity IS '嚴重度：critical / warning / info';
COMMENT ON COLUMN anomalies.confidence IS '信心分數 0-100';
COMMENT ON COLUMN anomalies.evidence IS 'JSONB 證據物件（URL、價格、效能等）';
COMMENT ON COLUMN anomalies.alerted IS '是否已發送 LINE 推播';
COMMENT ON COLUMN anomalies.alert_sent_at IS 'LINE 推播實際發送時間';
