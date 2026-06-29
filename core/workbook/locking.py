import os
import time
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class LockTimeoutError(Exception):
    """Raised when a lock cannot be acquired within the specified timeout."""
    pass

@contextmanager
def workbook_lock(workbook_path: str, timeout: int = 15):
    """
    Acquires an exclusive, file-based lock for a given workbook path.
    Prevents concurrent modifications to the same Excel file.
    
    Args:
        workbook_path: The absolute path to the workbook file.
        timeout: Maximum seconds to wait for the lock.
        
    Raises:
        LockTimeoutError: If the lock cannot be acquired before timeout.
    """
    lock_file_path = f"{workbook_path}.lock"
    start_time = time.time()
    
    fd = None
    while True:
        try:
            # os.O_CREAT | os.O_EXCL ensures atomic file creation.
            # This will raise FileExistsError if the lock file already exists.
            fd = os.open(lock_file_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            break
        except FileExistsError:
            if time.time() - start_time >= timeout:
                raise LockTimeoutError(f"Could not acquire lock for {workbook_path} within {timeout}s.")
            time.sleep(0.1)
        except OSError as e:
            logger.error(f"Error acquiring lock {lock_file_path}: {e}")
            raise
            
    try:
        yield
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
            
            try:
                os.remove(lock_file_path)
            except OSError:
                logger.warning(f"Failed to remove lock file {lock_file_path}")
