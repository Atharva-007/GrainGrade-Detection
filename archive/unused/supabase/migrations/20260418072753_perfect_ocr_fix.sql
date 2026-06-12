-- 1. Add scanned_image_url column to farmer_surveys
ALTER TABLE farmer_surveys 
ADD COLUMN IF NOT EXISTS scanned_image_url text;
-- 2. Create storage bucket for survey scans
INSERT INTO storage.buckets (id, name, public)
VALUES ('survey-scans', 'survey-scans', true)
ON CONFLICT (id) DO NOTHING;
-- 3. Set up Storage Policies (Safe version)
DO $$ 
BEGIN
    -- Public Read
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public Read' AND tablename = 'objects' AND schemaname = 'storage') THEN
        CREATE POLICY "Public Read" ON storage.objects FOR SELECT USING (bucket_id = 'survey-scans');
    END IF;

    -- Authenticated Upload
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Authenticated Upload' AND tablename = 'objects' AND schemaname = 'storage') THEN
        CREATE POLICY "Authenticated Upload" ON storage.objects FOR INSERT TO authenticated WITH CHECK (bucket_id = 'survey-scans');
    END IF;

    -- Authenticated Delete/Update
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Authenticated Modify' AND tablename = 'objects' AND schemaname = 'storage') THEN
        CREATE POLICY "Authenticated Modify" ON storage.objects FOR ALL TO authenticated USING (bucket_id = 'survey-scans');
    END IF;
END $$;
-- 4. Reload PostgREST cache
NOTIFY pgrst, 'reload schema';
