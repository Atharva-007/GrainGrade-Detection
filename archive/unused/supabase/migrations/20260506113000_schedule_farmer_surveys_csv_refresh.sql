create extension if not exists pg_cron;
create extension if not exists pg_net;
create extension if not exists supabase_vault;

do $$
declare
  project_url_secret_id uuid;
  anon_key_secret_id uuid;
begin
  select id
  into project_url_secret_id
  from vault.decrypted_secrets
  where name = 'farmer_surveys_project_url'
  limit 1;

  if project_url_secret_id is null then
    perform vault.create_secret(
      'https://hjgevqhpmcuwieqtorfj.supabase.co',
      'farmer_surveys_project_url',
      'Project URL for farmer_surveys CSV refresh cron'
    );
  else
    perform vault.update_secret(
      project_url_secret_id,
      'https://hjgevqhpmcuwieqtorfj.supabase.co',
      'farmer_surveys_project_url',
      'Project URL for farmer_surveys CSV refresh cron'
    );
  end if;

  select id
  into anon_key_secret_id
  from vault.decrypted_secrets
  where name = 'farmer_surveys_anon_key'
  limit 1;

  if anon_key_secret_id is null then
    perform vault.create_secret(
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhqZ2V2cWhwbWN1d2llcXRvcmZqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE5MzYwNTMsImV4cCI6MjA4NzUxMjA1M30.WbIz4Uq39NjQqqTCO819Al3niiDxcIJkvO_1bG6k5OI',
      'farmer_surveys_anon_key',
      'Anon JWT for farmer_surveys CSV refresh cron'
    );
  else
    perform vault.update_secret(
      anon_key_secret_id,
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhqZ2V2cWhwbWN1d2llcXRvcmZqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE5MzYwNTMsImV4cCI6MjA4NzUxMjA1M30.WbIz4Uq39NjQqqTCO819Al3niiDxcIJkvO_1bG6k5OI',
      'farmer_surveys_anon_key',
      'Anon JWT for farmer_surveys CSV refresh cron'
    );
  end if;
end $$;

select cron.schedule(
  'refresh-farmer-surveys-csv-every-15-minutes',
  '*/15 * * * *',
  $cron$
  select net.http_post(
    url := (
      select decrypted_secret
      from vault.decrypted_secrets
      where name = 'farmer_surveys_project_url'
      limit 1
    ) || '/functions/v1/farmer_surveys',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || (
        select decrypted_secret
        from vault.decrypted_secrets
        where name = 'farmer_surveys_anon_key'
        limit 1
      ),
      'apikey', (
        select decrypted_secret
        from vault.decrypted_secrets
        where name = 'farmer_surveys_anon_key'
        limit 1
      )
    ),
    body := jsonb_build_object(
      'source', 'pg_cron',
      'scheduled_at', now()
    ),
    timeout_milliseconds := 10000
  ) as request_id;
  $cron$
);
