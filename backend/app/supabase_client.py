from supabase import create_client, Client
from .config import settings

# Publishable/anon client: used only to validate user JWTs.
auth_client: Client = create_client(settings.supabase_url, settings.supabase_anon_key)

# Service-role client: server-side only. Never expose this key to the browser.
admin_client: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)
