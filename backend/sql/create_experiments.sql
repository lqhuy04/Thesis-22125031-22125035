CREATE TABLE IF NOT EXISTS experiments (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    experiment_type TEXT NOT NULL
        CHECK (experiment_type IN ('backtest', 'analysis')),
    status TEXT NOT NULL
        CHECK (status IN ('running', 'completed', 'failed')),
    scope TEXT NOT NULL,
    symbol TEXT,
    mode TEXT NOT NULL,
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    reproducibility JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_summary JSONB,
    result_data JSONB,
    result_reference TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    duration_ms BIGINT
);

ALTER TABLE experiments ADD COLUMN IF NOT EXISTS
    reproducibility JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_experiments_user_created
    ON experiments (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_experiments_user_type_status
    ON experiments (user_id, experiment_type, status);

-- Backend uses the privileged PostgreSQL pool. With no public RLS policy,
-- Supabase/PostgREST clients cannot read another user's experiment directly.
ALTER TABLE experiments ENABLE ROW LEVEL SECURITY;
