from fastapi import FastAPI
from pydantic import BaseModel
import math

from src.agent import ParcelPilotAgent


app = FastAPI(
    title="ParcelPilot AI Agent API"
)


# =========================================
# SESSION-BASED AGENTS
# =========================================

agents = {}


class QueryRequest(BaseModel):
    query: str
    session_id: str
    account_id: str | None = None
    order_id: str | None = None
    ticket_id: str | None = None


# =========================================
# GET AGENT FOR SESSION
# =========================================

def get_agent(session_id: str):

    if session_id not in agents:

        agents[session_id] = ParcelPilotAgent()

    return agents[session_id]


# =========================================
# CLEAN NaN VALUES
# =========================================

def clean_nan(data):

    if isinstance(data, float) and math.isnan(data):
        return None

    if isinstance(data, dict):

        return {
            key: clean_nan(value)
            for key, value in data.items()
        }

    if isinstance(data, list):

        return [
            clean_nan(item)
            for item in data
        ]

    return data


# =========================================
# HOME
# =========================================

@app.get("/")
def home():

    return {
        "message": "ParcelPilot AI Agent API is running"
    }


# =========================================
# PROCESS QUERY
# =========================================

@app.post("/query")
def process_query(request: QueryRequest):

    agent = get_agent(
        request.session_id
    )

    result = agent.process(
        query=request.query,
        account_id=request.account_id,
        order_id=request.order_id,
        ticket_id=request.ticket_id
    )

    return clean_nan(result)