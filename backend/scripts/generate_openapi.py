import json
import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

def generate_openapi_spec():
    openapi_schema = app.openapi()
    
    # Save to api/openapi/openapi.json
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    api_openapi_path = os.path.join(root_dir, "api", "openapi", "openapi.json")
    docs_openapi_path = os.path.join(root_dir, "docs", "openapi.json")
    
    os.makedirs(os.path.dirname(api_openapi_path), exist_ok=True)
    os.makedirs(os.path.dirname(docs_openapi_path), exist_ok=True)
    
    with open(api_openapi_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
        
    with open(docs_openapi_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
        
    print(f"Successfully generated OpenAPI specification at:\n - {api_openapi_path}\n - {docs_openapi_path}")

if __name__ == "__main__":
    generate_openapi_spec()
