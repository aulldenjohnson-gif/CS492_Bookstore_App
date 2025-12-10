import urllib.request
import time

time.sleep(2)  # wait for server
try:
    response = urllib.request.urlopen('http://127.0.0.1:5000/test')
    print("SUCCESS: Server responded")
    print(response.read().decode())
except Exception as e:
    print(f"ERROR: {e}")
