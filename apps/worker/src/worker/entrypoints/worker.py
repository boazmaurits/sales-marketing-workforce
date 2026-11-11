import asyncio
import os
import mistralai.workflows as workflows

async def main():
    api_key = os.environ.get("MISTRAL_API_KEY")
    workflow_classes = workflows.discover_all_workflows_in_package("worker.workflows")
    await workflows.run_worker(workflow_classes, api_key=api_key)

if __name__ == "__main__":
    asyncio.run(main())
