from dotenv import load_dotenv
import os, json

load_dotenv(dotenv_path=".env")

creds = json.loads(os.environ['FIREBASE_CREDENTIALS_JSON'])
print("✅ JSON cargado correctamente")
print("project_id:", creds['project_id'])
