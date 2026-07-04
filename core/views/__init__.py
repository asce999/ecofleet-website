from core.views.public import home, services, contact, about, privacy, sitemap, find_location
from core.views.portal_auth import portal_login, portal_logout
from core.views.portal_views import dashboard, portal_users
from core.views.common import download_file, tool_result
from core.views.cof import cof_generator, cof_workbook, cof_success, cof_history, cof_workbook_download
from core.views.btpl import get_active_btpl_workbook, btpl_sheet, btpl_api, btpl_download, btpl_settings
from core.views.ftl import get_active_ftl_workbook, ftl_sheet, ftl_api, ftl_download, ftl_settings
from core.views.attendance import attendance_sheet, attendance_download, attendance_settings, salary_calculator, salary_calculator_export
from core.views.tracking import *
from core.views.morning import morning_report
from core.views.pendency import pendency_report, pendency_observations
from core.views.prev_month import prev_month_update
from core.views.observability import health_check, sentry_debug, operations_center
