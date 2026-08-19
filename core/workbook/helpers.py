import io
import logging
from openpyxl import Workbook
from django.core.files.base import ContentFile
from django.db import models

logger = logging.getLogger(__name__)

def save_workbook_to_model(wb: Workbook, model_instance: models.Model, field_name: str = 'file', filename: str = None):
    """
    Saves an openpyxl Workbook to an in-memory buffer, then assigns it directly 
    to a Django model's FileField. This avoids relying on the local filesystem.
    """
    try:
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        file_field = getattr(model_instance, field_name)
        
        # Keep the original filename if one exists and none was provided
        if not filename and file_field and file_field.name:
            import os
            filename = os.path.basename(file_field.name)
        elif not filename:
            filename = 'workbook.xlsx'
            
        file_field.save(filename, ContentFile(buffer.getvalue()), save=True)
    except Exception as e:
        logger.error(f"Error saving workbook to model {model_instance}: {e}")
        raise
