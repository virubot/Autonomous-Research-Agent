from backend.tools.search import web_search
import json

print("Testing web_search...")
result = web_search("quantum computing", max_results=2)
print(json.dumps(result, indent=2))
