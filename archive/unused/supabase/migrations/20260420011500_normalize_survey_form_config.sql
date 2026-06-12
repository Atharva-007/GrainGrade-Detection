-- Normalize dynamic form config to match Flutter renderer input types.
-- This keeps survey fields visible and storable for current app versions.

-- 1) Normalize unsupported input types.
UPDATE form_fields
SET input_type = 'multiselect_checkbox'
WHERE field_key = 'millet_seed_type'
  AND input_type = 'multiselect';
UPDATE form_fields
SET input_type = 'acre'
WHERE field_key = 'land_under_millet'
  AND input_type = 'millet_land_picker';
-- 2) Keep disease section non-blocking and readable.
UPDATE form_fields
SET
  label = CASE field_key
    WHEN 'disease_present' THEN 'Any Disease Observed?'
    WHEN 'disease_name' THEN 'Disease Name'
    WHEN 'affected_crop' THEN 'Affected Crop'
    WHEN 'disease_severity' THEN 'Disease Severity'
    WHEN 'symptoms_observed' THEN 'Symptoms Observed'
    WHEN 'treatment_taken' THEN 'Treatment Taken'
    ELSE label
  END,
  is_required = false
WHERE field_key IN (
  'disease_present',
  'disease_name',
  'affected_crop',
  'disease_severity',
  'symptoms_observed',
  'treatment_taken'
);
-- 3) Ensure disease visibility rules are present for child fields.
UPDATE form_fields
SET visibility_rule = '{"depends_on":"disease_present","operator":"equals","value":true}'::jsonb
WHERE field_key IN (
  'disease_name',
  'affected_crop',
  'disease_severity',
  'symptoms_observed',
  'treatment_taken'
);
-- 4) Ensure disease severity options exist.
INSERT INTO dropdown_options (option_key, value, sort_order, is_active)
SELECT v.option_key, v.value, v.sort_order, true
FROM (
  VALUES
    ('disease_severity', 'Mild', 1),
    ('disease_severity', 'Moderate', 2),
    ('disease_severity', 'Severe', 3)
) AS v(option_key, value, sort_order)
WHERE NOT EXISTS (
  SELECT 1
  FROM dropdown_options d
  WHERE d.option_key = v.option_key
    AND d.value = v.value
);
NOTIFY pgrst, 'reload schema';
