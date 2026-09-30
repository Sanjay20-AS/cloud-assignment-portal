import os
import sys
from pathlib import Path

os.environ.setdefault('SUPABASE_URL', 'https://example.supabase.co')
os.environ.setdefault('SUPABASE_ANON_KEY', 'test-anon-key')
os.environ.setdefault('SUPABASE_SERVICE_ROLE_KEY', 'test-service-role-key')
os.environ.setdefault('FRONTEND_URL', 'http://localhost:5173')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
