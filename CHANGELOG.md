# Changelog

All notable changes to the MiMi project will be documented in this file.

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