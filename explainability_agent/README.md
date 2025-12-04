# Chargeback Recovery Rate Explainability Agent

This project implements an autonomous AI agent using **LangGraph** to diagnose and explain why a merchant's chargeback recovery rate has diminished for a specific period.

The agent mimics the workflow of a human data analyst by starting with a high-level view, identifying anomalies, and iteratively drilling down into the data until it isolates a root cause.

## How It Works

The agent operates on a cyclical graph where it continuously refines its understanding of the data:

1.  **Plan:** The agent's "Planner" node examines the current state of the investigation. It starts by looking at broad dimensions (e.g., `CARD_SCHEME`).
2.  **Execute:** It calls a "Tool" node to query the data, grouped by the chosen dimension. In this project, the Snowflake query is mocked for demonstration purposes.
3.  **Analyze & Loop:** The Planner analyzes the query results. If it identifies a broad segment with a poor recovery rate and significant volume, it formulates a hypothesis and decides to **drill down**. It adds a new dimension to the query (e.g., `INTEGRATION_NAME`) while filtering for the problematic segment (e.g., `CARD_SCHEME = 'visa'`). This loop continues, getting more granular with each cycle.
4.  **Conclude & Report:** Once the Planner identifies a specific, actionable root cause (or can't drill down any further), it exits the loop. A final "Reporter" node synthesizes the entire investigation log into a clear, human-readable summary.

## Project Structure

The project is organized into several key files within the `explainability_agent/` directory:

* `main.py`: The main entry point to start the analysis. It initializes the agent's state and prints the final report.
* `graph.py`: The core of the agent. It defines the graph's nodes (Planner, Tool, Reporter), the conditional logic (edges), and compiles them into a runnable LangGraph application.
* `state.py`: Defines the `AnalysisState` `TypedDict`, which acts as the graph's memory, holding all information about the investigation as it progresses.
* `tools.py`: Contains the `run_chargeback_analysis_query` tool. This is where the connection to a real database (like Snowflake) would be implemented. Currently, it uses a mock data generator.
* `prompts.py`: Stores the detailed system prompts for the AI-powered nodes (Planner and Reporter), guiding their reasoning and output format.
* `config.py`: Manages environment variables, specifically the `OPENAI_API_KEY`.

## Setup and Installation

Follow these steps to set up and run the agent on your local machine.

### 1. Prerequisites

* Python 3.8+

### 2. Installation

Clone the repository and install the required dependencies:

```bash
git clone <your-repo-url>
cd explainability_agent
pip install -r requirements.txt