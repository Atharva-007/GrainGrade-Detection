-- 1. Add scanned_image_url column to farmer_surveys
ALTER TABLE farmer_surveys 
ADD COLUMN IF NOT EXISTS scanned_image_url text;
-- 2. Create a bucket for survey scans if it doesn't exist
INSERT INTO storage.buckets (id, name, public)
VALUES ('survey-scans', 'survey-scans', true)
ON CONFLICT (id) DO NOTHING;
-- 3. Set up storage policies for the bucket
-- Allow public access to read (since it's a public bucket)
CREATE POLICY "Public Access" 
ON storage.objects FOR SELECT 
USING (bucket_id = 'survey-scans');
-- Allow authenticated users to upload
CREATE POLICY "Authenticated Upload" 
ON storage.objects FOR INSERT 
TO authenticated 
WITH CHECK (bucket_id = 'survey-scans');
-- Allow authenticated users to update/delete their own uploads
CREATE POLICY "Authenticated Update" 
ON storage.objects FOR UPDATE 
TO authenticated 
USING (bucket_id = 'survey-scans');
CREATE POLICY "Authenticated Delete" 
ON storage.objects FOR DELETE 
TO authenticated 
USING (bucket_id = 'survey-scans');
-- 4. Refresh schema cache
NOTIFY pgrst, 'reload schema';
