import random
import requests
from urllib.parse import urlparse
import requests

class RotatingProxyPool:
    def __init__(self, domain="p.webshare.io", port=80, username="gdcalran-rotate", password="hv3q4mmj42cq", file_path='proxy_list.txt'):
        """
        Initialize the rotating proxy pool with Webshare credentials.
        
        Args:
            domain (str): Proxy domain
            port (int): Proxy port number
            username (str): Proxy username
            password (str): Proxy password
        """
        self.proxies = self.load_proxies(file_path)
        self.index = random.randint(0, len(self.proxies) - 1) if self.proxies else 0
        self.port = port
        self.username = username
        self.password = password
        self.domain = domain
        self.proxy_url = f"http://{username}:{password}@{domain}:{port}"

    def load_proxies(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return [':'.join(line.strip().split(':')[:2]) for line in file if line.strip()]
        except FileNotFoundError:
            print(f"Error: {file_path} not found.")
            return []
        
    def get_file_proxy(self):
        if not self.proxies:
            return None
        proxy = self.proxies[self.index]
        self.index = (self.index + 1) % len(self.proxies)
        formatted_proxy = f"http://{self.username}:{self.password}@{proxy}"
        print(formatted_proxy)
        return {
            'http': formatted_proxy,
            'https': formatted_proxy
        }
        
    def get_proxy(self):
        """
        Returns proxy configuration dictionary for use with requests library.
        Each call will use Webshare's rotating proxy system.
        
        Returns:
            dict: Proxy configuration for requests
        """
        response = requests.get(
            "https://ipv4.webshare.io/",
            proxies={
                "http": self.proxy_url,
                "https": self.proxy_url
            }
        )
        ip = response.text
        formatted_proxy = f"http://{self.username}:{self.password}@{ip}:8080"
        return {
            'http': formatted_proxy,
            'https': formatted_proxy
        }
    
    def test_file_proxy(self):
        """
        Test if the proxy connection is working by making a request to an IP checking service.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            proxies = self.get_file_proxy()
            response = requests.get('http://ip-api.com/json', proxies=proxies)
            if response.status_code == 200:
                data = response.json()
                print(data)
                return True
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
        return False
    
    def test_connection(self):
        """
        Test if the proxy connection is working by making a request to an IP checking service.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            proxies = self.get_proxy()
            response = requests.get('http://ip-api.com/json', proxies=proxies)
            if response.status_code == 200:
                data = response.text
                print(data)
                return True
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    proxy_pool = RotatingProxyPool()

    proxy_pool.test_connection()