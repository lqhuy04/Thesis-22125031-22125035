
from agentic_ai.analyze.graph import build_graph
from agentic_ai.analyze.state import AgentState

def analyze(state: AgentState) -> dict:
    """Full pipeline cho một pipeline intent."""
    _graph = build_graph()

    initial_state = {
        "mode": "auto",
        
        "user_input": state['user_input'],
        "risk_appetite": state['risk_appetite'],

        "symbol": state["symbol"],

        "plan": {},
        "agent_results": {},

        "final_output": "",
        "error": None,
    }

    result = _graph.invoke(initial_state)

    if result.get("error"):
        raise RuntimeError(result["error"])

    return result["final_output"]