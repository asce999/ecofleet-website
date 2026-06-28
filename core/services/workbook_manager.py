import shutil
from pathlib import Path
from django.conf import settings

class WorkbookManager:
    @staticmethod
    def load_default_template(tool_name: str, template_filename: str) -> str:
        """
        Locates the default template for a given tool and copies it to the media directory.
        Returns the relative media path for Django's FileField.
        """
        source_path = Path(settings.BASE_DIR) / template_filename
        target_dir = Path(settings.MEDIA_ROOT) / tool_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = target_dir / template_filename
        shutil.copy2(source_path, dest_path)
        
        return f"{tool_name}/{template_filename}"

    @staticmethod
    def get_file_stream(wb_obj, fallback_template: str):
        """
        Returns a file stream for a workbook object, or the fallback template if none exists.
        Returns None if the fallback does not exist.
        """
        if wb_obj and hasattr(wb_obj, 'file') and wb_obj.file:
            try:
                return wb_obj.file.open('rb')
            except Exception:
                pass
                
        fallback_path = Path(settings.BASE_DIR) / fallback_template
        if fallback_path.exists():
            return open(fallback_path, 'rb')
            
        return None

