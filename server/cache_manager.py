import threading
import time
from datetime import datetime, timedelta

class CacheManager:
    """
    A simple thread-safe cache manager with time-to-live (TTL) support.
    """
    def __init__(self, ttl_seconds=60):
        self.cache = {}
        self.lock = threading.Lock()
        self.ttl = timedelta(seconds=ttl_seconds)

    def get(self, key):
        """
        Get a value from the cache. Returns None if the key is not found or has expired.
        """
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if datetime.now() < entry['expiry']:
                    return entry['value']
                else:
                    # Expired entry, remove it
                    del self.cache[key]
        return None

    def set(self, key, value):
        """
        Set a value in the cache with a TTL.
        """
        with self.lock:
            expiry = datetime.now() + self.ttl
            self.cache[key] = {'value': value, 'expiry': expiry}

    def start_background_fetch(self, key, fetch_function, *args, **kwargs):
        """
        Starts a background thread to fetch data and update the cache.
        `fetch_function` is the function that will be called to get the data.
        """
        def task():
            data = fetch_function(*args, **kwargs)
            if data:
                self.set(key, data)

        thread = threading.Thread(target=task)
        thread.daemon = True
        thread.start()

# Global cache manager instance
cache_manager = CacheManager()
