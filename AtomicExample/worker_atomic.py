import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio import workflow
import logging

with workflow.unsafe.imports_passed_through():
    # Workflow Import
    from workflow_atomic import AtomicUconWorkflow
    

    # Ucon Import
    from activities_ucon import (
        notify_external_system, check_opa_policy, get_user_data
    )

async def main():
    
    # Configure logging so that it logs the activity.logger.info function calls in the activities
    # logging.basicConfig(level=logging.INFO)

    client = await Client.connect("localhost:7233")

    # All Activities List
    all_activities = [
        notify_external_system, check_opa_policy, get_user_data
    ]

    worker = Worker(
        client,
        task_queue="loan-task-queue", # Could be multiple queues for multiple workers, i.e. one worker for the staff swimlane and one for the rest
        workflows=[AtomicUconWorkflow],
        activities=all_activities,
    )
    print("Worker started.")
    await worker.run()

if __name__ == "__main__":
    
    asyncio.run(main())