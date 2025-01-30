import requests
from proxies import proxies

def test_proxy(proxy):
    url = "https://www.facebook.com"
    proxies = {"http": proxy, "https": proxy}
    try:
        response = requests.get(url, proxies=proxies, timeout=10)
        if response.status_code == 200:
            print(f"Proxy {proxy} is working.")
            return True
        else:
            print(f"Proxy {proxy} failed with status code {response.status_code}.")
    except Exception as e:
        print(f"Proxy {proxy} failed")
        return False
    return False

working_proxies = [proxy for proxy in proxies if test_proxy(proxy)]
print(f"Working proxies: {working_proxies}")
