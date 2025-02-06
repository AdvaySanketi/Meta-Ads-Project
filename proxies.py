import os
import random
from dotenv import load_dotenv
import requests

class ProxyPool:
    def __init__(self, username, password, domain, port):
        """
        Initialize the rotating proxy pool with Webshare credentials.
        
        Args:
            domain (str): Proxy domain
            port (int): Proxy port number
            username (str): Proxy username
            password (str): Proxy password
        """
        self.proxy_url = f"http://{username}:{password}@{domain}:{port}"
        self.index = random.randint(0, 100 - 1)
        self.headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0'
        }

    def get_proxy(self):
        """
        Returns proxy configuration dictionary for use with requests library.
        Each call will use Webshare's rotating proxy system.
        
        Returns:
            dict: Proxy configuration for requests
        """
        return {
            "http": self.proxy_url,
            "https": self.proxy_url,
        }
    
    def test_connection(self):
        """
        Test if the proxy connection is working by making a request to an IP checking service.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            proxies = self.get_proxy()
            print(proxies)
            response = requests.get('http://ip-api.com/json', proxies=proxies,
            headers=self.headers, 
            timeout=20)
            if response.status_code == 200:
                data = response.text
                print(data)
                return True
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    load_dotenv()
    proxy_pool = ProxyPool(
        username=os.getenv("PROXY_USERNAME"),
        password=os.getenv("PROXY_PWD"),
        domain=os.getenv("PROXY_DOMAIN"),
        port=os.getenv("PROXY_PORT")
    )
    proxy_pool.test_connection()