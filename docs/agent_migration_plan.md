# MiMi Agent Migration Plan

This document outlines the plan for migrating agent classes from `mimi.core.software_agents.py` to individual files in the `mimi.core.agents` package.

## Progress

- [x] Add deprecation warnings to `agent.py` and `software_agents.py`
- [x] Create `ResearchAnalystAgent` in `mimi/core/agents/research_analyst_agent.py`
- [x] Create `ArchitectAgent` in `mimi/core/agents/architect_agent.py`
- [x] Update `mimi/core/agents/__init__.py` to export the new agent classes
- [x] Update imports in `mimi/core/project.py` to use the new agent classes
- [x] Create `SoftwareEngineerAgent` in `mimi/core/agents/software_engineer_agent.py`
- [x] Create `QAEngineerAgent` in `mimi/core/agents/qa_engineer_agent.py`
- [x] Create `ReviewerAgent` in `mimi/core/agents/reviewer_agent.py`
- [x] Update tests to use the new agent classes
- [x] Update imports in all other files that use the agent classes

## Remaining Tasks

- [ ] Completely phase out `software_agents.py` once all agent classes have been migrated
- [ ] Add the shared utility functions from `software_agents.py` to appropriate modules

## Implementation Strategy

1. **One agent at a time**: Migrate one agent class at a time, ensuring tests pass after each migration
2. **Backward compatibility**: Maintain backward compatibility during migration by keeping both implementations
3. **Update imports**: Update imports to use the new agent classes once they are implemented
4. **Remove old code**: Once all agent classes have been migrated, remove `software_agents.py`

## Utility Functions

The following utility functions from `software_agents.py` need to be properly handled:

- `get_project_directory`: Currently duplicated in each agent file, should be centralized
- All functions from `mimi.utils.output_manager` should be used directly 