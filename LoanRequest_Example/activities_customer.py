from temporalio import activity
import asyncio

@activity.defn
async def fulfil_loan_info(info: dict) -> dict:
    activity.logger.info(f"Running fulfil_loan_info with parameter {info}")
    user = info.get("user", "unknown")
    amount = info.get("amount", 0)
    loan_request = {'user':user, 'amount':amount}
    # await asyncio.sleep(30)
    return loan_request

@activity.defn
async def request_a_loan(loan_request: dict) -> dict:
    activity.logger.info(f"Running request_a_loan with parameter {loan_request}")
    return loan_request

@activity.defn
async def receive_notification(notification: dict) -> dict:
    activity.logger.info(f"Running receive_notification with parameter {notification}") 
    msg = notification.get('msg','No message attached')
    approved = notification.get('approved',False)
    result = {'msg':msg, 'approved':approved}
    return result

@activity.defn
async def send_ack_receipt(notification: dict) -> dict:
    activity.logger.info(f"Running send_ack_receipt with parameter {notification}") 
    now = datetime.now(timezone.utc)
    time_str = notification.get("time", None)    
    if time_str:
        notification_time = datetime.fromisoformat(time_str)
        delta = now - notification_time
        time_diff_days = delta.days
    else:
        time_diff_days = 0    
    ack = {'ack':True, 'notification':notification, 'days': time_diff_days}
    return ack