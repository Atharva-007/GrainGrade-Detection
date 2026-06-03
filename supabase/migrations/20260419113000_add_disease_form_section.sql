-- 1. Add disease columns to farmer_surveys
ALTER TABLE farmer_surveys
ADD COLUMN IF NOT EXISTS disease_present boolean,
ADD COLUMN IF NOT EXISTS disease_name text,
ADD COLUMN IF NOT EXISTS affected_crop text,
ADD COLUMN IF NOT EXISTS disease_severity text,
ADD COLUMN IF NOT EXISTS symptoms_observed text,
ADD COLUMN IF NOT EXISTS treatment_taken text;
-- 2. Add disease section if missing
INSERT INTO form_sections (title, icon_name, sort_order, is_active)
SELECT
  'Disease',
  'eco_outlined',
  COALESCE((SELECT MAX(sort_order) + 1 FROM form_sections), 1),
  true
WHERE NOT EXISTS (
  SELECT 1
  FROM form_sections
  WHERE lower(title) = 'disease'
);
-- 3. Add disease fields under disease section
WITH disease_section AS (
  SELECT id
  FROM form_sections
  WHERE lower(title) = 'disease'
  LIMIT 1
)
INSERT INTO form_fields (
  section_id,
  field_key,
  label,
  input_type,
  sort_order,
  is_required,
  validation,
  visibility_rule,
  dropdown_options_key,
  hint_text
)
SELECT
  ds.id,
  v.field_key,
  v.label,
  v.input_type,
  v.sort_order,
  v.is_required,
  v.validation,
  v.visibility_rule,
  v.dropdown_options_key,
  v.hint_text
FROM disease_section ds
CROSS JOIN (
  VALUES
    (
      'disease_present',
      'disease_present',
      'boolean',
      1,
      false,
      '{}'::jsonb,
      null::jsonb,
      null::text,
      null::text
    ),
    (
      'disease_name',
      'disease_name',
      'text',
      2,
      true,
      '{"min_length": 2}'::jsonb,
      '{"depends_on":"disease_present","operator":"equals","value":true}'::jsonb,
      null::text,
      'e.g. Blast, Rust, Smut'
    ),
    (
      'affected_crop',
      'affected_crop',
      'text',
      3,
      false,
      '{}'::jsonb,
      '{"depends_on":"disease_present","operator":"equals","value":true}'::jsonb,
      null::text,
      'Enter crop name'
    ),
    (
      'disease_severity',
      'disease_severity',
      'dropdown',
      4,
      true,
      '{}'::jsonb,
      '{"depends_on":"disease_present","operator":"equals","value":true}'::jsonb,
      'disease_severity',
      null::text
    ),
    (
      'symptoms_observed',
      'symptoms_observed',
      'text',
      5,
      false,
      '{}'::jsonb,
      '{"depends_on":"disease_present","operator":"equals","value":true}'::jsonb,
      null::text,
      'Write key symptoms'
    ),
    (
      'treatment_taken',
      'treatment_taken',
      'text',
      6,
      false,
      '{}'::jsonb,
      '{"depends_on":"disease_present","operator":"equals","value":true}'::jsonb,
      null::text,
      'Fungicide, biocontrol, etc.'
    )
) AS v(
  field_key,
  label,
  input_type,
  sort_order,
  is_required,
  validation,
  visibility_rule,
  dropdown_options_key,
  hint_text
)
WHERE NOT EXISTS (
  SELECT 1
  FROM form_fields ff
  WHERE ff.field_key = v.field_key
);
-- 4. Add dropdown options for disease severity
INSERT INTO dropdown_options (option_key, value, sort_order, is_active)
SELECT x.option_key, x.value, x.sort_order, true
FROM (
  VALUES
    ('disease_severity', 'Mild', 1),
    ('disease_severity', 'Moderate', 2),
    ('disease_severity', 'Severe', 3)
) AS x(option_key, value, sort_order)
WHERE NOT EXISTS (
  SELECT 1
  FROM dropdown_options d
  WHERE d.option_key = x.option_key
    AND d.value = x.value
);
-- 5. Reload PostgREST schema cache
NOTIFY pgrst, 'reload schema';
