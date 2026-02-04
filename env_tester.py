import os
from dotenv import load_dotenv

print("Starting ENV test...")
load_dotenv()

print("MYSQL_HOST:", os.getenv("MYSQL_HOST"))
print("MYSQL_PORT:", os.getenv("MYSQL_PORT"))
print("MYSQL_USER:", os.getenv("MYSQL_USER"))
print("MYSQL_PASSWORD exists:", bool(os.getenv("MYSQL_PASSWORD")))
print("MYSQL_DB:", os.getenv("MYSQL_DB"))

print("LASTFM_API_KEY exists:", bool(os.getenv("LASTFM_API_KEY")))
print("LASTFM_API_SECRET exists:", bool(os.getenv("LASTFM_API_SECRET")))

print("ENV test PASSED (check values above match as expected)")
