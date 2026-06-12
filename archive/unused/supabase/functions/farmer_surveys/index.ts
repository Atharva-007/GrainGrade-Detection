import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function jsonResponse(status: number, body: Record<string, unknown>) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      ...corsHeaders,
      "Content-Type": "application/json",
    },
  });
}

console.info("farmer_surveys CSV updater started");

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return jsonResponse(405, { error: "Method not allowed. Use POST." });
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

  if (!supabaseUrl || !serviceRoleKey) {
    return jsonResponse(500, {
      error: "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY",
    });
  }

  const supabaseAdmin = createClient(supabaseUrl, serviceRoleKey, {
    auth: {
      persistSession: false,
    },
  });

  const { data: csvData, error: fetchError } = await supabaseAdmin
    .from("farmer_surveys")
    .select("*")
    .csv();

  if (fetchError) {
    console.error("Fetch Error:", fetchError.message);
    return jsonResponse(500, { error: fetchError.message });
  }

  const filePath = "farmer_surveys_latest.csv";
  const csvBody = new Blob([csvData ?? ""], { type: "text/csv" });

  const { error: uploadError } = await supabaseAdmin.storage
    .from("survey_forms")
    .upload(filePath, csvBody, {
      contentType: "text/csv",
      upsert: true,
    });

  if (uploadError) {
    console.error("Upload Error:", uploadError.message);
    return jsonResponse(500, { error: uploadError.message });
  }

  return jsonResponse(200, {
    message: "farmer_surveys_latest.csv successfully updated",
    bucket: "survey_forms",
    path: filePath,
  });
});
