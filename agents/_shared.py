"""Shared helpers for building the LLM agents - prompt loading, the local
model config, and skill loading, kept in one place so it's easy to point at a
different LM Studio model or add a new skill later.
"""

from pathlib import Path

from google.adk.models.lite_llm import LiteLlm
from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

SHARED_CONVENTIONS_SKILL = "png-classroom-conventions"


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def get_local_model() -> LiteLlm:
    return LiteLlm(
        model="openai/gemma-4-e2b-it-qat",
        api_base="http://localhost:1234/v1",
        api_key="lm-studio",
    )


def build_skill_toolset(*task_skill_names: str) -> SkillToolset:
    """Builds a SkillToolset scoped to the shared PNG conventions skill plus
    the task-specific skill(s) named - never the full skill library - so each
    agent only ever sees the skill(s) relevant to its own job.
    """
    skill_names = [SHARED_CONVENTIONS_SKILL, *task_skill_names]
    skills = [load_skill_from_dir(SKILLS_DIR / name) for name in skill_names]
    return SkillToolset(skills=skills)
