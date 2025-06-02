import logging
from pathlib import Path
from ..agents.base_agent import Agent

class SecurityEngineerAgent(Agent):
    """
    Security Engineer Agent for security analysis and testing.
    """
    
    def execute(self, input_data):
        """
        Execute the security engineer agent.

        Args:
            input_data: Input data containing project requirements, path, etc.

        Returns:
            dict: Result of the execution
        """
        try:
            # Extract project directory and requirements
            if isinstance(input_data, dict) and 'project_dir' in input_data:
                project_dir = input_data['project_dir']
            else:
                # Use a default project directory if not provided
                project_dir = Path("Software")

            # Extract requirements from input data
            requirements = self._extract_requirements(input_data)
            
            # Perform security analysis
            security_analysis = self._perform_security_analysis(requirements)
            
            # Write security analysis to file
            self.write_log_to_file(
                project_dir=project_dir,
                content=security_analysis,
                subfolder="docs",
                filename="security_analysis.md"
            )
            
            # Log this action to the project log
            self.log_to_agent_file(
                project_dir=project_dir,
                action_type="security-analysis",
                input_summary=f"Project requirements for security analysis",
                output_summary=f"Generated security analysis report",
                details={
                    "security_file": "docs/security_analysis.md",
                    "agent_role": self.role
                }
            )
            
            # Return success
            return {
                "success": True,
                "message": f"{self.name} successfully performed security analysis",
                "security_analysis": security_analysis
            }
        except Exception as e:
            logging.error(f"{self.name} execution failed: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "security_analysis": None
            }
    
    def _extract_requirements(self, input_data):
        """
        Extract requirements from input data.
        
        Args:
            input_data: Input data in various formats
            
        Returns:
            str: Extracted requirements
        """
        logging.debug(f"Extracting requirements from input data of type: {type(input_data)}")
        
        if isinstance(input_data, dict):
            if 'input' in input_data:
                if isinstance(input_data['input'], dict) and 'input' in input_data['input']:
                    return input_data['input']['input']
                return str(input_data['input'])
            return str(input_data)
        return str(input_data)
    
    def _perform_security_analysis(self, requirements):
        """
        Perform security analysis based on requirements.
        
        Args:
            requirements: Project requirements
            
        Returns:
            str: Security analysis in markdown format
        """
        # For demonstration, generate a generic security analysis
        return """# Security Analysis Report

## Overview
This security analysis evaluates the Flappy Bird game implementation for potential security vulnerabilities and provides recommendations for secure implementation.

## Security Evaluation

### Client-Side Security
| Area | Risk Level | Description |
|------|------------|-------------|
| User Input | Low | Limited user input reduces attack surface |
| Browser Storage | Low | High scores stored in localStorage present minimal risk |
| DOM Manipulation | Low | Limited DOM manipulation with Canvas-based rendering |

### Network Security
| Area | Risk Level | Description |
|------|------------|-------------|
| Data Transmission | N/A | No server communication in current implementation |
| API Security | N/A | No APIs used in current implementation |

## Recommendations

1. **Input Validation**: Ensure any user input (even limited) is properly validated
2. **Storage Security**: Consider encryption for localStorage if storing sensitive data in future versions
3. **Resource Loading**: If adding external resources, use integrity checks and HTTPS
4. **Third-Party Libraries**: If adding external libraries, verify their security and keep them updated

## Conclusion
The current implementation has a minimal attack surface due to its client-side only nature. Implementing the recommendations will help maintain security as the application evolves.
""" 