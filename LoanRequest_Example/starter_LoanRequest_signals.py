import asyncio
import uuid
from temporalio.client import Client
from temporalio import workflow

async def main():
    client = await Client.connect("localhost:7233")

    loan_id = f"req-{uuid.uuid4().hex[:8]}" # For the loan and workflow

    # Initial Data Payload
    # Whole data needed initialized, in a real environment the data would come from the corresponding DBs
    loan_data = {
        # LoanRequest Data
        "loan_request": {
            # Direct attributes
            "id": loan_id,
            "amount": 25000.00,
            "accepted": False,
            "pending": True,
            "cost": 1000.00,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "account": "ES12345678901234567890",
            "loanTerms": True,        # preB1
            "notified": False,
        
            
            # Subfields

            # Requesting customer data
            "customer": {
                "id": "cust-ale-01",
                "name": "Ale",
                "lastName": "Vera",
                "email": "aleverbla@alum.us.es",
                "institution": "Universidad de Sevilla",
                "remuneration": 4000.00,      # preA1: (remuneration - costs) > remuneration/2
                "lastAccess": datetime.now(timezone.utc).isoformat(),
                "credentials": {              
                    "validated": True,
                    "revoked": False          # onA0
                }
            },
        
            # GPDR Agreement
            "gpdrAgreement": {
                "gpdrValidated": True         # preB0
            },
        
            # Customer Account
            "customerAccount": {
                "accountNumber": "ES12345678901234567890",
                "balance": 5000.00
            },

            # Credit Supplier
            "creditSupplier": {
                "id": "supplier-01",
                "name": "Bank 01",
                "address": "-, Sevilla"
            },
        },
        
        # Customer and workflow history
        "history": {
            "active_loans": 2,    # preA3
            "tasks_done": []      # preA0: To be filled with (task,user_it_was_done_by_id)
        },
        
        # Loan Request Report
        "report": {
            "lastAccess": None,
            "rate": 0.0,
            "sent": False,
            "risk": None  # ("VERY LOW"/"LOW"/"MEDIUM"/"HIGH"/"VERY HIGH")
        },

        # Mock environment, would be gotten from the HTTP header
        "environment": {
            "device_type": "desktop",     # preC0 ("desktop"/"mobile")
            "current_time": "10:00:00"    # onC0
        }
    }


    # Workflow ID
    workflow_id = f"loan-workflow-{loan_id}"

    print(f"Starting Loan Request for {loan_data['user']}...")

    result = await client.execute_workflow(
        "LoanRequestWorkflowSignals",
        loan_data,
        id=workflow_id,
        task_queue="loan-task-queue",
    )

    print("--- Loan Request Ended ---")
    print(f"Workflow Result: {result}")
    print(f"Notification Result: {result.get('notification', {}).get('msg', 'No Message')}")

if __name__ == "__main__":
    asyncio.run(main())