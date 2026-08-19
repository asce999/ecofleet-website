import time
import logging
import hashlib
from contextlib import contextmanager
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class LockTimeoutError(Exception):
    """Raised when a lock cannot be acquired within the specified timeout."""
    pass

@contextmanager
def workbook_lock(identifier: str, timeout: int = 15):
    """
    Acquires an exclusive, Redis-backed lock for a given workbook identifier.
    Prevents concurrent modifications to the same Excel file across instances.
    
    Args:
        identifier: A unique string identifier for the lock (e.g. file path or model ID).
        timeout: Maximum seconds to wait for the lock.
        
    Raises:
        LockTimeoutError: If the lock cannot be acquired before timeout.
    """
    # Create a safe key hash to avoid memcached/redis key restrictions
    safe_id = hashlib.md5(str(identifier).encode('utf-8')).hexdigest()
    lock_key = f"workbook_lock_{safe_id}"
    
    start_time = time.time()
    lock_timeout_settings = getattr(settings, 'WORKBOOK_LOCK_TIMEOUT', 120)
    
    acquired = False
    while True:
        # cache.add returns True if the key didn't exist and was set atomically
        acquired = cache.add(lock_key, "locked", lock_timeout_settings)
        if acquired:
            break
            
        if time.time() - start_time >= timeout:
            raise LockTimeoutError(f"Could not acquire lock for {identifier} within {timeout}s.")
            
        time.sleep(0.1)
            
    try:
        yield
    finally:
        if acquired:
            cache.delete(lock_key)

