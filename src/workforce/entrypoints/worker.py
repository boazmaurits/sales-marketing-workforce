"""
Sales & Marketing Workforce - Worker Entry Point
Runs all 8 agents as a Mistral workflow worker
"""

import asyncio
import os
import logging
import mistralai.workflows as workflows

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the workflow worker."""
    logger.info("🚀 Starting Sales & Marketing Workforce Worker...")
    
    # Get API key from environment
    api_key = os.environ.get("MISTRAL_API_KEY")
    
    # Discover all workflows in the workforce package
    workflow_classes = workflows.discover_all_workflows_in_package("workforce.workflows")
    
    logger.info(f"✅ Discovered {len(workflow_classes)} workflow(s)")
    for wf in workflow_classes:
        logger.info(f"  - {wf.__name__}")
    
    # Run the worker
    logger.info("🏃 Starting worker...")
    await workflows.run_worker(workflow_classes, api_key=api_key)


if __name__ == "__main__":
    asyncio.run(main())
