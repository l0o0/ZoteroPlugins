import os
import requests

# 
token = os.getenv("TOKEN")
headers = {
    "authorization": "Bearer %s" % token,
    "content-type": "application/json"
}

resp = requests.get("https://api.github.com/repos/l0o0/jasminum", headers=headers)
print(resp.json)
