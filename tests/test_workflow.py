#!/usr/bin/env python3
import pytest
from workflows.sales_marketing_workforce import SalesMarketingWorkflow

@pytest.mark.asyncio
async def test_workflow():
    workflow = SalesMarketingWorkflow()
    await workflow.run()
    assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])