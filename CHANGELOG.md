# Changelog

All notable changes to the MiMi project will be documented in this file.

## [1.1.2] - 2025-06-02

### Fixed
- **QA Agent Input Handling**: Fixed input format mismatch that prevented QA agents from processing advanced project tasks
  - Issue: QA agents in advanced projects received `integrated_frontend` and `integrated_backend` input keys but only recognized `integrated_system`, `fixed_system`, and `implementation` keys
  - Root cause: Naming mismatch between project task configuration and QAEngineerAgent implementation
  - Solution: Added support for `integrated_frontend` and `integrated_backend` input keys in QAEngineerAgent.execute() method
  - Affected files: `mimi/core/agents/qa_engineer_agent.py`
  - Both new handlers call `_test_system()` method with appropriate logging for specialized frontend/backend testing
  - Enhanced error handling with better debugging information including available input keys
  - Added comprehensive test suite in `tests/test_qa_engineer_agent.py` with 9 test cases covering all input scenarios
  - Fix maintains backward compatibility and follows established codebase patterns

## [1.1.1] - 2025-06-02

### Fixed
- **Critical Logging Issue**: Fixed KeyError "'input'" in logging system that prevented task execution
  - Issue occurred when logging complex nested data containing curly braces (e.g., `{'input': {'input': '...', 'project_dir': ...}}`)
  - Root cause: loguru logger interpreted ALL curly braces in log messages as string formatting placeholders
  - Solution: Implemented consistent brace escaping using `str(data).replace("{", "{{").replace("}", "}}")` pattern
  - Affected files: `mimi/core/task.py:164`, `mimi/core/runner.py:232`, `mimi/__main__.py:123`
  - Added comprehensive test suite in `tests/test_logging_fix.py` with 7 test cases covering edge cases
  - Fix follows established patterns already used in logger utility functions (`agent_log`, `task_log`, `project_log`)

## [1.1.0] - 2025-05-05

### Added
- Multi-step workflow where each agent performs calculations multiple times
- Enhanced NumberAdderAgent with repetitions parameter and step tracking
- Step-by-step verification in AnalystAgent for detailed validation
- Comprehensive multi-step feedback from FeedbackProcessorAgent
- Advanced example project demonstrating multi-step calculations

### Changed
- Improved verification to analyze each step in a calculation sequence
- Enhanced feedback with detailed step information
- Updated README with advanced workflow documentation
- Refined error detection and reporting to identify specific steps with issues

## [1.0.0] - 2025-05-03

### Added
- Verification system with AnalystAgent for verifying calculations
- FeedbackProcessorAgent for providing human-readable feedback
- Immediate verification workflow that verifies each step
- Error detection and workflow control based on verification results
- Comprehensive documentation for verification features
- Tests for verification agents

### Changed
- Improved data handling in tasks to prevent data accumulation
- Enhanced agent execution to better filter irrelevant data
- Updated README with verification workflow details
- Refactored code for better maintainability

### Fixed
- Prevented issue where all previous calculations were being re-verified
- Fixed data flow between verification steps
- Improved error handling and reporting

## [0.9.0] - 2025-04-15

### Added
- Initial implementation of multi-agent workflow
- NumberAdderAgent for performing addition operations
- YAML-based configuration for projects, agents and tasks
- Task dependencies and execution order management
- Ollama integration for model access
- Comprehensive logging system 