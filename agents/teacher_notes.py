from google.adk.agents import LlmAgent

from agents._shared import build_skill_toolset, load_prompt

OUTPUT_KEY = "teacher_notes_raw"


def build_teacher_notes_agent(model) -> LlmAgent:
    return LlmAgent(
        name="teacher_notes_agent",
        model=model,
        description="Generates teacher-facing notes (concepts, worked examples, common mistakes) for the topic.",
        instruction=load_prompt("teacher_notes"),
        tools=[build_skill_toolset("teacher-notes-writing")],
        output_key=OUTPUT_KEY,
        include_contents="none",
    )
