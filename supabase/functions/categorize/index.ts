// supabase/functions/categorize/index.ts

import { serve } from "https://deno.land/std@0.203.0/http/server.ts";
import { createClient, SupabaseClient } from "https://esm.sh/@supabase/supabase-js@2.35.0?target=deno";


// Environment variables (use global Deno object, do NOT import anything)
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const AI_ENDPOINT = Deno.env.get("AI_ENDPOINT")!;

// Initialize Supabase client
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

// Start Edge Function
serve(async (req) => {
  try {
    const { complaint_id } = await req.json() as { complaint_id: number };

    if (!complaint_id) {
      return new Response(JSON.stringify({ error: "complaint_id is required" }), { status: 400 });
    }

    const { data: complaint, error: fetchError } = await supabase
      .from("complaints")
      .select("*")
      .eq("id", complaint_id)
      .single();

    if (fetchError || !complaint) {
      return new Response(JSON.stringify({ error: "Complaint not found" }), { status: 404 });
    }

    const aiResp = await fetch(AI_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_url: complaint.file_url,
        title: complaint.title,
        description: complaint.description,
      }),
    });

    if (!aiResp.ok) {
      return new Response(JSON.stringify({ error: "AI service failed" }), { status: 502 });
    }

    const aiData: { category_id: number; confidence: number } = await aiResp.json();

    const { error: updateError } = await supabase
      .from("complaints")
      .update({
        category_id: aiData.category_id,
        is_ai_categorized: true,
        confidence_score: aiData.confidence,
      })
      .eq("id", complaint_id);

    if (updateError) {
      return new Response(JSON.stringify({ error: "Failed to update complaint" }), { status: 500 });
    }

    return new Response(JSON.stringify({ ok: true, ai: aiData }), { status: 200 });
  } catch (err) {
    console.error(err);
    return new Response(JSON.stringify({ error: "Internal Server Error" }), { status: 500 });
  }
});
