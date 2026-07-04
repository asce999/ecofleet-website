from celery import shared_task
from core.importers.excel_importer import ExcelImporter
from core.importers.btpl_importer import BtplImporter
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_ftl_import(import_job_id, file_path):
    logger.info(f"Starting Celery task for FTL import job {import_job_id}")
    importer = ExcelImporter()
    importer.process_ftl_workbook(import_job_id, file_path)

@shared_task
def process_btpl_import(import_job_id, file_path):
    logger.info(f"Starting Celery task for BTPL import job {import_job_id}")
    importer = BtplImporter()
    importer.process_btpl_workbook(import_job_id, file_path)
