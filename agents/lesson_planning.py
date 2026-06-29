from google.adk.agents import LlmAgent

from agents._shared import build_skill_toolset, load_prompt

OUTPUT_KEY = "lesson_plan_raw"


def build_lesson_planning_agent(model) -> LlmAgent:
    return LlmAgent(
        name="lesson_planning_agent",
        model=model,
        description="Generates a PNG lesson plan, for whichever grade/subject the request specifies, from a matched curriculum record.",
        instruction=load_prompt("lesson_planning"),
        tools=[build_skill_toolset("lesson-plan-writing")],
        output_key=OUTPUT_KEY,
        include_contents="none",
    )
