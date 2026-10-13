from kite_agent.agent_core import AgentConfig, to_ollama_tools


def test_fingerprint_deterministic():
    a = AgentConfig(system_prompt="hi", temperature=0.2, max_steps=6)
    b = AgentConfig(system_prompt="hi", temperature=0.2, max_steps=6)
    assert a.fingerprint() == b.fingerprint()


def test_fingerprint_varies_by_temp():
    a = AgentConfig(system_prompt="hi", temperature=0.2)
    b = AgentConfig(system_prompt="hi", temperature=0.9)
    assert a.fingerprint() != b.fingerprint()


def test_fingerprint_varies_by_prompt():
    a = AgentConfig(system_prompt="a")
    b = AgentConfig(system_prompt="b")
    assert a.fingerprint() != b.fingerprint()


def test_to_ollama_tools_shape():
    class T:
        name = "foo"
        description = "does foo"
        inputSchema = {"type": "object", "properties": {}}

    class R:
        tools = [T()]

    assert to_ollama_tools(R()) == [
        {
            "type": "function",
            "function": {
                "name": "foo",
                "description": "does foo",
                "parameters": {"type": "object", "properties": {}},
            },
        }
    ]
