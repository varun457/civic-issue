import os
from supabase import create_client
from dotenv import load_dotenv

# Load the .env file so the keys become available to os.environ
load_dotenv()

# Use os.getenv so we don't crash if something is missing
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Optional: fail early with a clear error if variables are missing
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Missing Supabase credentials. Check that .env exists at the project root "
        "and contains SUPABASE_URL and SUPABASE_KEY."
    )

# Create the Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
