-- 1. Add the composite JSON column to farmer_surveys
ALTER TABLE farmer_surveys
ADD COLUMN IF NOT EXISTS cropping_pattern jsonb;
-- 2. Create the detailed tracking table for multi-season crops
CREATE TABLE IF NOT EXISTS survey_cropping_patterns (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  survey_id uuid NOT NULL REFERENCES farmer_surveys(id) ON DELETE CASCADE,
  season text NOT NULL CHECK (season IN ('kharif', 'rabi')),
  crop_name text NOT NULL,
  seed_type text,
  fertilizer_type text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);
-- 3. Enable RLS and permissions
ALTER TABLE survey_cropping_patterns ENABLE ROW LEVEL SECURITY;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'survey_cropping_patterns'
      AND policyname = 'Allow all for authenticated users'
  ) THEN
    CREATE POLICY "Allow all for authenticated users"
    ON survey_cropping_patterns FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);
  END IF;
END $$;
-- 4. Notify PostgREST to reload the schema cache
NOTIFY pgrst, 'reload schema';
