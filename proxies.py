import random

proxies = [
    '202.140.62.212:8080', 
    '45.89.65.240:3128', 
    '203.144.144.146:8080', 
    '162.212.153.169:8888', 
    '171.237.237.218:10003', 
    '212.113.101.232:30520', 
    '200.174.198.86:8888', 
    '223.206.146.147:8080', 
    '160.22.193.142:8080'
]

class ProxyPool:
    def __init__(self):
        self.proxies = proxies
        self.index = random.randint(0, 9)

    def get_proxy(self):
        proxy = self.proxies[self.index]
        self.index = (self.index + 1) % len(self.proxies)
        return proxy