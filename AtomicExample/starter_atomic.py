import asyncio
import uuid
from temporalio.client import Client

async def main():
    # Connect to Temporal server
    client = await Client.connect("localhost:7233")

    # Generate ID
    test_id = f"test-{uuid.uuid4().hex[:8]}"

    # Data for the input
    atomic_data = {
        "object": {
            "id": test_id,
            "descripcion": "Test Object for the atomic UCON example",
        },
        
        # Simulated environment with fields and the history
        "environment": {
            "time_hour": 10,  
            "device_type": "desktop",
            "history": {
                "tasks_done": []
            }
        }
    }

    workflow_id = f"atomic-workflow-{test_id}"

    print(f"Starting atomic workflow {test_id} with the following data:\n {atomic_data}...")

    # Ejecutar el nuevo workflow
    result = await client.execute_workflow(
        "AtomicUconWorkflow",
        atomic_data,
        id=workflow_id,
        task_queue="loan-task-queue",
    )

    print("--- Atomic Workflow Executed ---")
    print(f"Activity B result: {result.get('final_result')}")
    print(f"Final history: {result.get('environment', {}).get('history', {}).get('tasks_done')}")

if __name__ == "__main__":
    asyncio.run(main())