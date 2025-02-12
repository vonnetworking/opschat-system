import pytest
from agents.main_agent import Agent

@pytest.mark.parametrize(
    "message",
    [
        ("What is the system IP?"), # Tests basic tool use
        ("What is the system time?"),  # Tests basic tool use
        ("Did any applications go down today?"),  # Test compound tool use
        ("What did Lady Gagga wear to the Grammies?"),  # Test out of scope query
    ]
)
def test_agent_generate_response(message):
    agent = Agent()  # Initialize the agent

    response = agent.generate_response(message)  # Invoke the agent with user input

    assert isinstance(response, str), "Response should be a string"