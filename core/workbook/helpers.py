import os
import shutil
import tempfile
import logging
from openpyxl import Workbook
from pathlib import Path

logger = logging.getLogger(__name__)

def atomic_save_workbook(wb: Workbook, target_path: str):
    """
    Saves an openpyxl Workbook to a temporary file first, then atomically 
    replaces the target_path. This prevents corruption if the process dies 
    mid-save.
    """
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    fd, temp_path = tempfile.mkstemp(dir=target_path.parent, suffix='.xlsx', prefix='tmp_wb_')
    os.close(fd)
    
    try:
        # Save to the temporary file
        wb.save(temp_path)
        
        # Atomically replace the target file
        os.replace(temp_path, target_path)
    except Exception as e:
        logger.error(f"Error during atomic save to {target_path}: {e}")
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise
