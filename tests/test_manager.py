# Copyright 2026 Ameen Saeed — Apache 2.0 License

"""Tests for ForkManager resilience features."""

import asyncio
import pytest

from thought_fork.config import ForkConfig
from thought_fork.fork import Fork
from thought_fork.manager import ForkManager


class MockClient:
    """A mock AsyncOpenAI client to simulate API behaviors."""
    
    def __init__(self, fail_count=0):
        self.fail_count = fail_count
        self.attempts = 0
        self.chat = self.MockChat(self)
        
    class MockChat:
        def __init__(self, parent):
            self.parent = parent
            
            class MockCompletions:
                def __init__(self, parent):
                    self.parent = parent
                    
                async def create(self, **kwargs):
                    self.parent.attempts += 1
                    if self.parent.attempts <= self.parent.fail_count:
                        raise Exception("Mock API failure")
                        
                    # Return a mock response
                    class MockMessage:
                        content = "Mock response"
                        
                    class MockChoice:
                        message = MockMessage()
                        
                    class MockUsage:
                        completion_tokens = 42
                        
                    class MockResponse:
                        choices = [MockChoice()]
                        usage = MockUsage()
                        
                    return MockResponse()
                    
            self.completions = MockCompletions(parent)
            



@pytest.mark.asyncio
async def test_manager_retries_and_succeeds():
    """Test that a failing API call is retried and eventually succeeds."""
    mock_client = MockClient(fail_count=2)
    config = ForkConfig(
        api_key="test-key",
        max_retries=3,
        client=mock_client
    )
    
    manager = ForkManager(config)
    fork = Fork(id="A", stance="cautious", system_prompt="Test prompt")
    
    result = await manager._run_single_fork(fork, "Test question")
    
    assert mock_client.attempts == 3  # Failed twice, succeeded on third try
    assert result.output == "Mock response"
    assert result.token_count == 42


@pytest.mark.asyncio
async def test_manager_graceful_degradation():
    """Test that a fork failing beyond max_retries gracefully marks the failure."""
    mock_client = MockClient(fail_count=5)  # Fails 5 times
    config = ForkConfig(
        api_key="test-key",
        max_retries=1,  # Only retry once
        client=mock_client
    )
    
    manager = ForkManager(config)
    fork = Fork(id="A", stance="cautious", system_prompt="Test prompt")
    
    # We patch asyncio.sleep so the test runs fast
    original_sleep = asyncio.sleep
    async def fast_sleep(t): pass
    asyncio.sleep = fast_sleep
    
    try:
        result = await manager._run_single_fork(fork, "Test question")
    finally:
        asyncio.sleep = original_sleep
        
    assert mock_client.attempts == 2  # 1 initial try + 1 retry
    assert "[Fork A failed:" in result.output
    assert result.token_count == 0


@pytest.mark.asyncio
async def test_manager_concurrency_limit():
    """Test that the semaphore actually limits concurrency."""
    # We use a custom mock client that sleeps so we can count active requests
    class SlowMockClient:
        active = 0
        max_active = 0
        
        class MockChat:
            class MockCompletions:
                async def create(self, **kwargs):
                    SlowMockClient.active += 1
                    SlowMockClient.max_active = max(SlowMockClient.max_active, SlowMockClient.active)
                    await asyncio.sleep(0.1)
                    SlowMockClient.active -= 1
                    
                    class MockMessage: content = "response"
                    class MockChoice: message = MockMessage()
                    class MockUsage: completion_tokens = 10
                    class MockResponse:
                        choices = [MockChoice()]
                        usage = MockUsage()
                    return MockResponse()
            completions = MockCompletions()
        chat = MockChat()

    config = ForkConfig(
        api_key="test-key",
        max_concurrent_forks=2,  # Limit to 2 concurrent forks
        client=SlowMockClient()
    )
    
    manager = ForkManager(config)
    forks = [Fork(id=str(i), stance="test", system_prompt="sys") for i in range(5)]
    
    await manager.run_parallel(forks, "prompt")
    
    # Even though we launched 5, max active at any time should be 2
    assert SlowMockClient.max_active == 2
