#!/usr/bin/env python3
"""
Sales & Marketing Workforce - Main Entry Point
Multi-agent system for automated lead generation and prospecting
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from mistralai.mcp.client import MCPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class SalesMarketingWorkforce:
    """Orchestrates the multi-agent sales and marketing workflow."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or "workflow.yaml")
        self.client: Optional[MCPClient] = None
        self.workflow_config: dict = self._load_config()

    def _load_config(self) -> dict:
        """Load workflow configuration from YAML file."""
        import yaml
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    async def run(self):
        """Run the complete sales and marketing workflow."""
        logger.info("🚀 Starting Sales & Marketing Workforce...")

        # Initialize MCP client for Mistral Studio
        self.client = MCPClient()

        # Import and run the workflow
        from workflows.sales_marketing_workforce import SalesMarketingWorkflow
        workflow = SalesMarketingWorkflow(client=self.client, config=self.workflow_config)
        await workflow.run()

        logger.info("✅ Workflow completed!")

    def deploy(self):
        """Deploy the workflow to Mistral Studio."""
        logger.info("📦 Deploying to Mistral Studio...")
        # Deployment logic will be handled by Mistral Studio
        print("\n" + "="*60)
        print("DEPLOYMENT INSTRUCTIONS:")
        print("="*60)
        print("1. Go to: https://studio.mistral.ai")
        print("2. Create a new Workflow deployment")
        print("3. Select this repository: boazmaurits/sales-marketing-workforce")
        print("4. Choose branch: main")
        print("5. Click Deploy")
        print("="*60 + "\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sales & Marketing Workforce")
    parser.add_argument("--config", type=str, help="Path to workflow config file")
    parser.add_argument("--deploy", action="store_true", help="Show deployment instructions")
    args = parser.parse_args()

    if args.deploy:
        SalesMarketingWorkforce().deploy()
    else:
        asyncio.run(SalesMarketingWorkforce(config_path=args.config).run())