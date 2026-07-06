from pydantic import BaseModel


class DecisionScenarioRead(BaseModel):
    title: str
    description: str
    icon: str


class FounderBriefingResponse(BaseModel):
    summary: str
    top_observations: list[str]
    business_risks: list[str]
    knowledge_gaps: list[str]
    recommended_actions: list[str]
    decision_scenarios: list[DecisionScenarioRead]
