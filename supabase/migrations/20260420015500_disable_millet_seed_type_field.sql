-- Remove millet seed type block from cropping pattern form config.
UPDATE form_fields
SET is_active = false
WHERE field_key = 'millet_seed_type';
NOTIFY pgrst, 'reload schema';
