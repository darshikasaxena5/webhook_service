import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise EnvironmentError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")

supabase: Client = create_client(supabase_url, supabase_key)

def get_db() -> Client:
    """Dependency function to get the Supabase client."""
    return supabase 