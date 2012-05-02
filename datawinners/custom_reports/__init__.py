from datawinners.custom_report_router.report_router import custom_report_routing_table
from datawinners.custom_reports.crs.handler import CRSCustomReportHandler
from datawinners.local_settings import CRS_ORG_ID

custom_report_routing_table[CRS_ORG_ID]=CRSCustomReportHandler()