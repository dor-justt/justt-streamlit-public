import json
from typing import Literal

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from explainability_agent.state import AnalysisState
from explainability_agent.tools import run_chargeback_analysis_query
from explainability_agent.prompts import PLANNER_PROMPT, REPORTER_PROMPT
from explainability_agent.config import OPENAI_API_KEY

# The model can be any chat model that supports function/tool calling and JSON mode
model = ChatOpenAI(temperature=0, model="gpt-4o", api_key=OPENAI_API_KEY)


def planner_node(state: AnalysisState) -> dict:
    """Decides the next action based on the investigation log."""
    print("--- 🧠 Planner Node ---")
    
    # Prune dimensions that are already in the query plan to avoid redundant suggestions
    potential_dims = [
        d for d in state['potential_dimensions'] 
        if d not in state['query_plan'].get('dimensions', [])
    ]

    prompt = PLANNER_PROMPT.format(
        investigation_log="\n".join(state['investigation_log']),
        potential_dimensions=", ".join(potential_dims)
    )
    
    response = model.invoke(prompt, response_format={"type": "json_object"})
    response_json = json.loads(response.content)

    thought = response_json.get("thought", "No thought provided.")
    action = response_json.get("action")
    
    log_entry = f"Planner Thought: {thought}"
    print(log_entry)

    if action == "conclude":
        return {"investigation_log": state['investigation_log'] + [log_entry], "final_report": "pending"}
    
    if isinstance(action, dict) and action.get("tool_name") == "run_chargeback_analysis_query":
        query_plan = action["parameters"]
        return {"investigation_log": state['investigation_log'] + [log_entry], "query_plan": query_plan}

    raise ValueError(f"Invalid action from planner: {action}")


def tool_node(state: AnalysisState) -> dict:
    """Executes the planned query tool."""
    query_plan = state["query_plan"]
    tool_output = run_chargeback_analysis_query(
        dimensions=query_plan.get("dimensions", []),
        filters=query_plan.get("filters", {}),
        state=state
    )
    
    log_entry = f"Tool Output:\n{tool_output}"
    
    return {"investigation_log": state['investigation_log'] + [log_entry]}


def report_node(state: AnalysisState) -> dict:
    """Generates the final report."""
    print("--- 📝 Report Node ---")
    prompt = REPORTER_PROMPT.format(investigation_log="\n".join(state["investigation_log"]))
    response = model.invoke(prompt)
    
    print(f"Final Report Generated:\n{response.content}")
    return {"final_report": response.content}


def should_continue(state: AnalysisState) -> Literal["continue", "end"]:
    """Conditional edge to decide whether to continue or end."""
    if state.get("final_report") == "pending":
        return "end"
    return "continue"

# Define the graph
workflow = StateGraph(AnalysisState)

workflow.add_node("planner", planner_node)
workflow.add_node("tool_executor", tool_node)
workflow.add_node("reporter", report_node)

workflow.set_entry_point("planner")

workflow.add_edge("tool_executor", "planner")

workflow.add_conditional_edges(
    "planner",
    should_continue,
    {
        "continue": "tool_executor",
        "end": "reporter",
    },
)

workflow.add_edge("reporter", END)

# Compile the graph with checkpointer
checkpointer = InMemorySaver()
app = workflow.compile(checkpointer=checkpointer)