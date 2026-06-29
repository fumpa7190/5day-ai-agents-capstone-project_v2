import pathlib

import pytest
from google.adk.skills import load_skill_from_dir

SKILLS_DIR = pathlib.Path(__file__).resolve().parent.parent / "skills"

SHARED_SKILL = "png-classroom-conventions"
TASK_SKILLS = [
    "lesson-plan-writing",
    "classroom-activities-writing",
    "teacher-notes-writing",
    "assessment-writing",
]
ALL_SKILLS = [SHARED_SKILL, *TASK_SKILLS]


@pytest.mark.parametrize("skill_name", ALL_SKILLS)
def test_skill_loads_cleanly(skill_name):
    # load_skill_from_dir parses frontmatter, validates the name matches the
    # directory name, and reads instructions/resources - any structural
    # problem with a SKILL.md raises here, so a clean load is itself the test.
    skill = load_skill_from_dir(SKILLS_DIR / skill_name)
    assert skill.name == skill_name
    assert skill.description
    assert skill.instructions.strip()


@pytest.mark.parametrize("skill_name", TASK_SKILLS)
def test_task_skill_has_template_asset(skill_name):
    # Every task-specific skill (not the shared conventions skill) defines
    # its output structure as a separate assets/template.md resource, loaded
    # via load_skill_resource rather than inlined in SKILL.md's instructions.
    skill = load_skill_from_dir(SKILLS_DIR / skill_name)
    assert "template.md" in skill.resources.list_assets()
    assert skill.resources.get_asset("template.md").strip()


def test_no_unexpected_skill_directories():
    actual = {p.name for p in SKILLS_DIR.iterdir() if p.is_dir()}
    assert actual == set(ALL_SKILLS)
