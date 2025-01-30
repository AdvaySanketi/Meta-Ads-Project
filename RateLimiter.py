import time
import threading
from functools import wraps

# Rate limiter decorator
class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = threading.Lock()

    def __call__(self, func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            with self.lock:
                now = time.time()
                self.calls = [c for c in self.calls if now - c < self.period]
                
                if len(self.calls) >= self.max_calls:
                    sleep_time = self.period - (now - self.calls[0])
                    if sleep_time > 0:
                        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: Rate limit reached. Sleeping for {sleep_time:.2f} seconds...")
                        time.sleep(sleep_time)
                
                self.calls.append(time.time())
            
            return func(*args, **kwargs)
        return wrapped
