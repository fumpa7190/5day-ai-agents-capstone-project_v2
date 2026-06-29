from google.adk.agents import LlmAgent

from agents._shared import build_skill_toolset, load_prompt

OUTPUT_KEY = "activities_raw"


def build_activities_agent(model) -> LlmAgent:
    return LlmAgent(
        name="activities_agent",
        model=model,
        description="Generates practical classroom activities for the matched lesson.",
        instruction=load_prompt("activities"),
        tools=[build_skill_toolset("classroom-activities-writing")],
        output_key=OUTPUT_KEY,
        include_contents="none",
    )
