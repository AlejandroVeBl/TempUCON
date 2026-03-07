from temporalio import activity

@activity.defn
async def receive_loan_request(loan_request: dict) -> dict:
    activity.logger.info(f"Running receive_loan_request with parameter {loan_request}")
    return loan_request

@activity.defn
async def evaluate_risk(loan_request: dict) -> dict:
    activity.logger.info(f"Running evaluate_risk with parameter {loan_request}")
    user = loan_request['user']
    amount=loan_request['amount']
    # Could be evaluated also using Rego OPA but I'm doing it inside here because it's an activity
    #---------- RISK TABLE ----------#
    # VERY LOW.........0
    # LOW.............25
    # MEDIUM..........50
    # HIGH............75
    # VERY HIGH......100
    #--------------------------------#
    # Bogus logic for risk evaluation
    risk = 50
    if user=="Ale":
        risk = 10
    if amount>10000:
        risk+=25
    if amount>100000:
        risk+=25
    loan_request_report = {'user':user, 'amount':amount, 'risk':risk}
    return loan_request_report

@activity.defn
async def send_rating_reports(loan_request_report: dict) -> dict:
    activity.logger.info(f"Running send_rating_reports with parameter {loan_request_report}")
    return loan_request_report