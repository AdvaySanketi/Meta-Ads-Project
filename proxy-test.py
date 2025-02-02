import requests
import sys
from proxies import ProxyPool

def test_proxy(proxy):
    url = "https://www.facebook.com"
    formatted_proxy = f"http://{proxy}"
    proxies = {"http": formatted_proxy, "https": formatted_proxy}
    
    try:
        response = requests.get(url, proxies=proxies, timeout=10)
        if response.status_code == 200:
            print(f"Proxy {proxy} is working.")
            return True
        else:
            print(f"Proxy {proxy} failed with status code {response.status_code}.")
    except Exception as e:
        print(f"Proxy {proxy} failed: {e}")
        return False
    return False

proxies = ProxyPool()
working_proxies = []

for proxy in proxies.proxies:
    parts = proxy.split(':')
    if len(parts) == 4:
        proxy_with_auth = f"{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
        if test_proxy(proxy_with_auth):
            working_proxies.append(proxy)

print(f"Working proxies: {len(working_proxies)}")