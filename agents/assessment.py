from google.adk.agents import LlmAgent

from agents._shared import build_skill_toolset, load_prompt

OUTPUT_KEY = "assessment_raw"


def build_assessment_agent(model) -> LlmAgent:
    return LlmAgent(
        name="assessment_agent",
        model=model,
        description="Generates assessment items (quiz/test/assignment) with a marking guide for the matched lesson.",
        instruction=load_prompt("assessment"),
        tools=[build_skill_toolset("assessment-writing")],
        output_key=OUTPUT_KEY,
        include_contents="none",
    )
