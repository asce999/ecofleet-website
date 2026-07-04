import os
import time
import logging
import psutil
from contextlib import contextmanager
from django.conf import settings

logger = logging.getLogger(__name__)

class LockTimeoutError(Exception):
    """Raised when a lock cannot be acquired within the specified timeout."""
    pass

def is_process_alive(pid: int) -> bool:
    try:
        return psutil.pid_exists(pid)
    except Exception:
        return False

@contextmanager
def workbook_lock(workbook_path: str, timeout: int = 15):
    """
    Acquires an exclusive, file-based lock for a given workbook path.
    Prevents concurrent modifications to the same Excel file.
    # ponytail: The filesystem lock will be retired in Sprint 5 when the DB becomes authoritative (or we migrate to a Redis lock). Do not touch for now.
    
    Args:
        workbook_path: The absolute path to the workbook file.
        timeout: Maximum seconds to wait for the lock.
        
    Raises:
        LockTimeoutError: If the lock cannot be acquired before timeout.
    """
    lock_file_path = f"{workbook_path}.lock"
    start_time = time.time()
    lock_timeout_settings = getattr(settings, 'WORKBOOK_LOCK_TIMEOUT', 120)
    
    my_pid = os.getpid()
    
    fd = None
    while True:
        try:
            # Try to atomically create the lock file
            fd = os.open(lock_file_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            # Write our PID to the lock file
            os.write(fd, str(my_pid).encode('utf-8'))
            break
        except FileExistsError:
            # The lock file exists. Check if it's stale.
            try:
                mtime = os.path.getmtime(lock_file_path)
                if time.time() - mtime > lock_timeout_settings:
                    logger.warning(f"Lock file {lock_file_path} is stale (TTL expired). Removing it.")
                    os.remove(lock_file_path)
                    continue  # Try acquiring again
                
                with open(lock_file_path, 'r') as f:
                    lock_pid = int(f.read().strip())
                
                if not is_process_alive(lock_pid):
                    logger.warning(f"Lock file {lock_file_path} owned by dead PID {lock_pid}. Removing it.")
                    os.remove(lock_file_path)
                    continue  # Try acquiring again
            except (OSError, ValueError):
                pass
                
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
