import asyncio
import os
import mistralai.workflows as workflows
from mistralai.client import Mistral

async def main():
    api_key = os.environ.get("MISTRAL_API_KEY")
    workflows_client = Mistral(api_key=api_key) if api_key else Mistral()
    workflow_classes = workflows.discover_all_workflows_in_package("worker.workflows")
    await workflows_client.run_worker(workflow_classes)

if __name__ == "__main__":
    asyncio.run(main())
