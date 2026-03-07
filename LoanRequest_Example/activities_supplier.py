from temporalio import activity

@activity.defn
async def collect_customer_information(loan_request: dict) -> dict:
    activity.logger.info(f"Running collect_customer_information with parameter {loan_request}")
    return loan_request

@activity.defn
async def request_report(loan_request: dict) -> dict:
    activity.logger.info(f"Running request_report with parameter {loan_request}")
    return loan_request

@activity.defn
async def collect_rating_reports(loan_request_report: dict) -> dict:
    activity.logger.info(f"Running collect_rating_reports with parameter {loan_request_report}")
    return loan_request_report

@activity.defn
async def send_negative_notification(notification: dict) -> dict:
    activity.logger.info(f"Running send_negative_notification with parameter {notification}")
    return notification

@activity.defn
async def send_approved_notification(notification: dict) -> dict:
    activity.logger.info(f"Running send_approved_notification with parameter {notification}")
    return notification

@activity.defn
async def open_loan_file(loan_request_report: dict) -> dict:
    activity.logger.info(f"Running open_loan_file with parameter {loan_request_report}")
    return loan_request_report

@activity.defn
async def close_loan_approval_file(loan_request_report: dict) -> dict:
    activity.logger.info(f"Running close_loan_approval_file with parameter {loan_request_report}")
    return loan_request_report
