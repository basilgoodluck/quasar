import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY           = os.getenv("SECRET_KEY", "")
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:4000/auth/google/callback")
FRONTEND_URL         = os.getenv("FRONTEND_URL", "http://localhost:3000")
ADMIN_EMAIL          = os.getenv("ADMIN_EMAIL", "")
REDIS_URL            = os.getenv("REDIS_URL", "redis://redis:6379")
POSTGRES_DB                 = os.getenv("POSTGRES_DB", "quasar")
POSTGRES_HOST               = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PASSWORD           = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_PORT               = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER               = os.getenv("POSTGRES_USER", "postgres")