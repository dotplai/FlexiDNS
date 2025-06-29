from typing import Self

import json
import math
import os
import time

class RecordsCache:
    def __init__(self) -> None:
        """
        Initializes a RecordsCache instance with a specified cache directory.

        The constructor creates the cache directory if it doesn't exist and sets the path for storing cache data.

        Args:
            cache_directory (str): The directory to store the cache data. Defaults to 'cache'.

        Example Usage:
        --------------
        ```
        cache = RecordsCache()
        cache.build({...})  # Build cache with preloaded data.
        ```
        """
        
    def build(self, cache_name: str = 'records', pre_data: dict = None, timeout: int = 86400, cache_directory: str = 'cache') -> Self:
        """
        Builds a new cache instance with optional preloaded data and a timeout.

        This method can only be called once, as it creates a single cache. If the cache is built, calling this
        method again will overwrite the existing cache.

        Args:
            cache_name (str): The name of the cache file to be created. Defaults to 'records'.
            pre_data (dict, optional): A dictionary of preloaded data to populate the cache. Defaults to None.
            timeout (int, optional): The timeout duration for cache entries in seconds. Defaults to 86400 (1 day).
            cache_directory (str, optional): The directory to store the cache data. Defaults to 'cache'.
        Returns:
            Self: The current instance of the `RecordsCache` with the cache built.

        Example Usage:
        --------------
        ```
        cache = RecordsCache().build()  # Build a new cache.
        print(cache.is_valid())  # Check if the cache is valid.
        # => True
        ```
        """
        os.makedirs(cache_directory, exist_ok=True)
        self.cache_record_path = os.path.join(cache_directory, f'{cache_name}.cache')
        
        self.timeout: int | float = timeout if timeout > 0 else math.inf
        current_time = time.time()
        if pre_data:
            pre_data["expiry_time"] = math.inf if math.isinf(self.timeout) else current_time + self.timeout
        
        self.cache_data = pre_data if pre_data else {}
        return self
    
    def update(self, update_data: dict, key: str = None) -> None:
        """
        Updates existing cache data with new data.

        If a `key` is provided, the method updates the specific entry; otherwise, it replaces the entire cache.

        Args:
            update_data (dict): The new data to be added or updated in the cache.
            key (str, optional): The key to identify which cache entry to update. Defaults to None.

        Raises:
            KeyError: If the specified key does not exist in the cache.

        Example Usage:
        --------------
        ```
        cache = RecordsCache().build({"key_544": {...}, "key_632": {...}})
        cache.update({"key_733": {...}, "key_462": {...}})
        print(cache.get())
        # => {"key_733": {...}, "key_462": {...}}
        ```
        """
        if key and key not in self.cache_data:
            raise KeyError(f"Key '{key}' does not exist in the cache.")
            
        current_time = time.time()
        update_data["expiry_time"] = math.inf if math.isinf(self.timeout) else current_time + self.timeout
        if not key:
            self.cache_data = update_data
        else:
            self.cache_data[key] = update_data
        
    def get(self, key: str = None) -> dict | None:
        """
        Retrieves the cached data if it's still valid. Returns `None` if expired or empty.

        If `key` is provided, it returns the data for the specific key if it's valid. Otherwise, it returns all
        valid cached data.

        Args:
            key (str, optional): The key to fetch specific cache data. Defaults to None.

        Returns:
            dict | None: The cached data for the given key, or all valid cached data.

        Raises:
            KeyError: If the cache is empty or the specified key does not exist in the cache.

        Example Usage:
        --------------
        ```
        cache = RecordsCache().build({"key_544": {...}, "key_632": {"y":32,...}})
        print(cache.get())
        # => { "key_544": {...}, "key_632": {"y":32,...} }
        print(cache.get("key_632"))
        # => {"y": 32,...} 
        ```
        """
        current_time = time.time()
        
        if not self.cache_data:
            raise KeyError("Cache is empty. Please build it first.")
        if key:
            if key not in self.cache_data:
                raise KeyError(f"Key '{key}' does not exist in the cache.")
            
            if self.cache_data[key]["expiry_time"] <= current_time:
                del self.cache_data[key]
            return None if key not in self.cache_data else self.cache_data[key]
        else:
            for k, v in list(self.cache_data.items()):
                if v["expiry_time"] <= current_time:
                    del self.cache_data[k]
            return self.cache_data

    def inject(self, key: str, update_data: dict) -> None:
        """
        Injects specific data into an existing cache entry under a unique key with the same expiry time.

        If the specified key is valid and the cache entry has not expired, the data is updated. Otherwise, a
        `ValueError` is raised.

        Args:
            key (str): The key of the cache entry to update.
            update_data (dict): The data to inject into the cache.

        Raises:
            KeyError: If the specified key does not exist in the cache.
            ValueError: If the cache entry has expired.

        Example Usage:
        --------------
        ```
        cache = RecordsCache().build({"key_544": {...}})
        cache.inject("key_544", {"new_data": {...}})
        ```
        """
        if key not in self.cache_data:
            raise KeyError(f"Key '{key}' does not exist in the cache.")
        
        current_time = time.time()
        if self.cache_data[key]["expiry_time"] > current_time:
            self.cache_data[key].update(update_data)
        else:
            del self.cache_data[key]
            raise ValueError(f"Cannot inject data into an expired key '{key}'.")

    def append(self, key: str, append_data: dict) -> None:
        """
        Appends additional data to the existing cache.

        This method adds the provided `append_data` to the cache under the specified `key`. If the key already exists,
        a `KeyError` is raised. The method also ensures that the cache entry has an `expiry_time` based on the
        configured `timeout`.

        Args:
            key (str): The key under which the data will be stored in the cache.
            append_data (dict): The data to append to the cache.

        Raises:
            ValueError: If the `cache_data` is not a dictionary.
            KeyError: If the key already exists in the cache.

        Example Usage:
        --------------
        ```
        cache = RecordsCache().build({"key_544": {...}, "key_632": {...}})
        
        cache.append("key_772", {...})
        
        print(cache.get())
        # => {"key_544": {...}, "key_632": {...}, "key_772": {...}}
        ```
        """
        if not isinstance(self.cache_data, dict):
            raise ValueError("Cache data must be a dictionary to append new items.")
        if key in self.cache_data:
            raise KeyError(f"Duplicate key '{key}' detected. Use `RecordsCache.update({append_data}, key='{key}')` to update the existing entry instead.")

        current_time = time.time()
        append_data["expiry_time"] = math.inf if math.isinf(self.timeout) else current_time + self.timeout

        self.cache_data[key] = append_data

    def delete(self, key: str) -> None:
        """
        Deletes a specific entry from the cache using the given key.

        This method removes the data associated with the specified `key` from the cache. If the key does not exist,
        it raises a `KeyError`.

        Args:
            key (str): The key identifying the cache entry to be deleted.

        Raises:
            KeyError: If the specified key does not exist in the cache.

        Example Usage:
        --------------
        ```
        cache = RecordsCache().build({"key_544": {...}, "key_632": {...}})
        
        cache.delete("key_632")
        
        print(cache.get())
        # => {"key_544": {...}}
        ```
        """
        if key not in self.cache_data:
            raise KeyError(f"Key '{key}' does not exist in the cache.")
        
        del self.cache_data[key]

        
    def commit(self) -> None:
        """
        Persists the cache data to a file.

        This method writes the current state of `cache_data` to the file specified by `cache_record_path`. It ensures that
        the cache data is saved and not lost, even if the program terminates unexpectedly. Use this method to manually save
        the cache data.

        Raises:
            AttributeError: If `cache_data` is empty or not initialized, indicating there is no data to commit.

        Example Usage:
        --------------
        ```
        cache = RecordsCache().build(pre_data={"key_112": {...}})
        cache.commit()
        ```
        """
        if not self.cache_data:
            raise AttributeError("Cache data is empty or not initialized. Nothing to commit.")

        with open(self.cache_record_path, "w") as f:
            json.dump(self.cache_data, f, indent=4)

    def pull(self) -> None:
        """
        Loads and caches the data from the file.

        This method reads data from the `cache_file` and stores it in the `cache_data` attribute as a dictionary.

        Raises:
            FileNotFoundError: If the `cache_file` does not exist, indicating data must be committed before pulling.

        Example Usage:
        --------------
        ```python
        cache = RecordsCache()
        cache.pull()
        data = cache.get()
        print(data)
        # => {...}
        ```
        """
        try:
            with open(self.cache_record_path, "rt") as f:
                data: dict = json.load(f)

                f.close()
        except FileNotFoundError:
            raise FileNotFoundError("Cache file not found. Make sure to commit data before pulling.")

        self.cache_data = data

    def read(self) -> dict:
        """
        Reads and returns data from the file.

        This method loads data from the `cache_file` and returns it as a dictionary.

        Raises:
            FileNotFoundError: If the `cache_file` does not exist, indicating data must be committed before reading.

        Example Usage:
        --------------
        ```python
        cache = RecordsCache()
        data = cache.read()
        print(data)
        # => {...}
        ```
        """
        try:
            with open(self.cache_record_path, "rt") as f:
                data: dict = json.load(f)

                f.close()
        except FileNotFoundError:
            raise FileNotFoundError("Cache file not found. Make sure to commit data before pulling.")

        return data


    def is_same(self, data: dict, with_expiry: bool = True) -> bool:
        """
        Compare the current cache data with the provided dictionary.

        This method checks if the `data` dictionary is equivalent to the 
        `cache_data` stored in the object. By default, it includes the `expiryTime` 
        values in the comparison. If `with_expiry` is set to `False`, 
        the comparison will exclude any keys named `expiryTime`.

        Args:
            data (dict): The dictionary to compare with the current cache data.
            with_expiry (bool): Whether to include `expiryTime` keys 
                                in the comparison. Defaults to True.

        Returns:
            bool: True if `data` is identical to `cache_data` (considering the 
                `with_expiry` parameter), False otherwise.

        Example Usage:
        ```python
        cache = RecordsCache().build(pre_data={
            "key_723": {"x": 112,},
            "key_665": {"x": 47}
        })
        
        a = {
            "key_723": {"x": 112},
            "key_665": {"x": 47}
        }
        b = {
            "key_723": {"x": 112},
            "key_665": {"x": 16}
        }
        c = {
            "key_723": {"x": 112},
            "key_665": {"x": 47}
        }

        print(cache.is_same(a))
        # => True
        print(cache.is_same(b))
        # => False
        print(cache.is_same(c))
        # => True
        ```
        """
        if not with_expiry:
            def __ret__(data) -> dict:
                """Remove `expiryTime` keys from the dictionary (non-recursive)."""
                return {
                    k: {sub_k: sub_v for sub_k, sub_v in v.items() if sub_k != "expiryTime"}
                    if isinstance(v, dict) else v
                    for k, v in data.items()
                }

            return __ret__(self.cache_data).__eq__(__ret__(data))
        return self.cache_data.__eq__(data)

    def is_empty(self) -> bool:
        """ 
        Check if the cache is empty. 
        
        Return True if the cache is empty, False otherwise.
        
        Example Usage:
        --------------
        ```
        cache = RecordsCache().build()
        print(cache.is_empty())
        # => True
        ```
        """
        return (not hasattr(self, "cache_data") or not self.cache_data or self.cache_data == {} or self.cache_data == None)
    
    def is_valid(self, key: str) -> bool:
        """
        Check if a specific cache entry is still valid (not expired).
        
        This method verifies whether the specified key exists in the cache and 
        whether its expiry time has not yet passed. If the key does not exist, 
        a `KeyError` is raised.

        Example Usage:
        --------------
        ```
        import time
        current_time = time.time()
        print(current_time)
        # => 200
        
        # Create a cache with a 60-second timeout.
        # "key_112" have expiry_time = 260
        cache = RecordsCache().build(pre_data={"key_112": {"expiry_time": current_time + 60}})

        # Check validity of the cache entry.
        print(cache.is_valid("key_112"))
        # => True (if called within 60 seconds, since it's not expired yet) 
        # => False (if called after 60 seconds, since it has expired)
        ```
        """
        
        if key not in self.cache_data:
            raise KeyError(f"Key '{key}' does not exist in the cache.")
            
        current_time = time.time()
        return self.cache_data[key]["expiry_time"] > current_time

    def is_exist(self, key: str) -> bool:
        """ Check if the cache key is exist. 
        
        return True if the cache key is exist, False otherwise. 
        
        Example Usage:
        --------------
        ```
        cache = RecordsCache().build(pre_data={"key_112": {...}})
        
        print(cache.is_exist("key_112"))
        # => True
        cache.delete("key_112")
        print(cache.is_exist("key_112"))
        # => False
        ```
        """
        
        return key in self.cache_data
     
    def poke(self) -> None:
        """ Clean up expired cache entries.
        
        Iterates through the cache data and removes any entries
        whose `expiry_time` has passed the current time.
        
        Example Usage:
        --------------
        ```
        import time
        
        current_time = time.time()
        print(current_time) 
        # => 200
        
        cache = RecordsCache().build(
            pre_data={
                    "key_112": {...,"expiry_time": current_time+60}, # 260
                    "key_113": {...,"expiry_time": current_time+90}, # 290
                }
            )
        
        # After 60 seconds passing...
        cache.poke()
        print(cache.get())
        # => {"key_113": {...,"expiry_time": 290}}
        ```
        """
        current_time = time.time()
        keys_to_delete = [k for k, v in self.cache_data.items() if isinstance(v, dict) and "expiry_time" in v and v["expiry_time"] <= current_time]
        
        for k in keys_to_delete:
            del self.cache_data[k]
