"""Minimal LangGraph experiment (not used by production orchestrator).

Requires optional deps: pip install -r requirements-dev.txt
"""
import asyncio
import uuid
from typing import Annotated, Any, TypedDict
from langgraph.graph import StateGraph, END, START

def _merge_lists(existing: list, new: list) -> list:
    return existing + new

def _replace_value(existing: Any, new: Any) -> Any:
    return new

class State(TypedDict):
    current_stage: Annotated[str, _replace_value]
    audit_log: Annotated[list[str], _merge_lists]

async def agent_node(state: State):
    print("--- AGENT NODE STARTING ---")
    return {
        "current_stage": "review",
        "audit_log": ["agent_finished"]
    }

def build_graph():
    graph = StateGraph(State)
    graph.add_node("agent", agent_node)
    graph.set_entry_point("agent")
    graph.add_edge("agent", END)
    return graph.compile()

async def main():
    print("Building graph...")
    compiled = build_graph()
    initial_state = {
        "current_stage": "start",
        "audit_log": ["started"]
    }
    print("Invoking graph...")
    result = await compiled.ainvoke(initial_state)
    print("Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
