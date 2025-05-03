"""Feedback processor agent for MiMi."""

from typing import Any, Dict, List, Optional

from mimi.utils.logger import agent_log

from mimi.core.agents.base_agent import Agent


class FeedbackProcessorAgent(Agent):
    """Agent that processes verification results from AnalystAgent."""
    
    def execute(self, task_input: Any) -> Any:
        """Process verification feedback and provide recommendations.
        
        Args:
            task_input: A dictionary containing verification results from the AnalystAgent.
            
        Returns:
            A dictionary with processed feedback and recommendations.
        """
        agent_log(self.name, "execute", f"Processing verification feedback: {str(task_input)}")
        
        try:
            # Find verification result
            verified_keys = []
            for key in task_input:
                if key.startswith("verified") and isinstance(task_input[key], dict):
                    verified_keys.append(key)
                    
            # Extract verification status
            status = None
            message = "No verification message provided"
            verification_results = []
            
            if verified_keys:
                # Get the most recent verification result
                latest_key = sorted(verified_keys, key=lambda k: int(k[8:]) if k[8:].isdigit() else 0)[-1]
                verified_data = task_input[latest_key]
                
                # Extract data from the verification result
                status = verified_data.get("status")
                message = verified_data.get("message", "No message provided")
                verification_results = verified_data.get("verification_results", [])
            
            # Initialize feedback structure
            feedback = {
                "original_status": status,
                "original_message": message,
                "summary": "",
                "errors_found": 0,
                "recommendations": [],
                "detailed_feedback": []
            }
            
            # If there are no verification results, return minimal feedback
            if not verification_results:
                feedback["summary"] = "No verification data was provided to analyze."
                feedback["recommendations"].append("Ensure verification agent is properly configured to return detailed results.")
                return feedback
            
            # Process each verification result
            for i, result in enumerate(verification_results):
                operation = result.get("operation", f"Operation {i+1}")
                is_correct = result.get("is_correct", False)
                expected = result.get("expected")
                actual = result.get("actual")
                steps = result.get("steps", [])
                
                # Build detailed feedback for this result
                result_feedback = {
                    "operation": operation,
                    "is_correct": is_correct,
                    "expected": expected,
                    "actual": actual,
                    "description": "",
                    "step_feedback": []
                }
                
                if is_correct:
                    result_feedback["description"] = f"✓ {operation} was performed correctly."
                    
                    # Check if there were any step errors despite correct final result
                    step_errors = [step for step in steps if not step.get("is_correct", True)]
                    if step_errors:
                        result_feedback["description"] += f" However, {len(step_errors)} intermediate step(s) had errors."
                        feedback["errors_found"] += len(step_errors)
                else:
                    # Build error description
                    if expected is not None and actual is not None:
                        error_desc = f"✗ {operation} produced an incorrect result. Expected {expected}, but got {actual}."
                    else:
                        error_desc = f"✗ {operation} produced an incorrect result."
                    
                    result_feedback["description"] = error_desc
                    feedback["errors_found"] += 1
                
                # Process step feedback if available
                if steps:
                    for step in steps:
                        step_num = step.get("step", "unknown")
                        step_op = step.get("operation", f"Step {step_num}")
                        step_correct = step.get("is_correct", False)
                        step_expected = step.get("expected")
                        step_actual = step.get("actual")
                        
                        step_feedback = {
                            "step": step_num,
                            "operation": step_op,
                            "is_correct": step_correct,
                            "expected": step_expected,
                            "actual": step_actual,
                            "description": ""
                        }
                        
                        if step_correct:
                            step_feedback["description"] = f"✓ {step_op} was performed correctly."
                        else:
                            if step_expected is not None and step_actual is not None:
                                step_feedback["description"] = f"✗ {step_op} produced an incorrect result. Expected {step_expected}, but got {step_actual}."
                            else:
                                step_feedback["description"] = f"✗ {step_op} produced an incorrect result."
                            
                        result_feedback["step_feedback"].append(step_feedback)
                
                feedback["detailed_feedback"].append(result_feedback)
            
            # Generate overall summary
            if feedback["errors_found"] == 0:
                feedback["summary"] = "All calculations were performed correctly."
                feedback["recommendations"].append("No changes needed. All operations verified successfully.")
            else:
                feedback["summary"] = f"Found {feedback['errors_found']} error(s) in the calculations."
                
                # Generate specific recommendations based on error patterns
                common_errors = self._analyze_error_patterns(feedback["detailed_feedback"])
                
                # Add recommendations based on common error types
                if "addition_errors" in common_errors and common_errors["addition_errors"]:
                    feedback["recommendations"].append("Review basic addition operations. Consider using a calculator for verification.")
                
                if "step_sequence_errors" in common_errors and common_errors["step_sequence_errors"]:
                    feedback["recommendations"].append("Ensure each step's starting value matches the previous step's result.")
                
                if "final_result_mismatch" in common_errors and common_errors["final_result_mismatch"]:
                    feedback["recommendations"].append("Double-check that the final reported result matches the result of the last calculation step.")
                
                if "rounding_errors" in common_errors and common_errors["rounding_errors"]:
                    feedback["recommendations"].append("Check for potential rounding errors in intermediate calculations.")
                
                # If no specific patterns were identified, add a generic recommendation
                if not feedback["recommendations"]:
                    feedback["recommendations"].append("Double-check all calculations with special attention to the operations flagged as incorrect.")
            
            agent_log(self.name, "execute", f"Feedback processing completed: {feedback['summary']}")
            return feedback
            
        except Exception as e:
            error_message = f"Error processing verification feedback: {str(e)}"
            agent_log(self.name, "error", error_message)
            return {
                "original_status": "error",
                "original_message": str(task_input.get("message", "Unknown")),
                "summary": "An error occurred while processing the verification results.",
                "errors_found": 0,
                "recommendations": ["Review the error message and try again."],
                "detailed_feedback": [],
                "error": str(e)
            }
    
    def _analyze_error_patterns(self, detailed_feedback: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Analyze the feedback to identify common error patterns.
        
        Args:
            detailed_feedback: List of detailed feedback items.
            
        Returns:
            Dictionary of identified error patterns.
        """
        patterns = {
            "addition_errors": False,
            "step_sequence_errors": False,
            "final_result_mismatch": False,
            "rounding_errors": False
        }
        
        for item in detailed_feedback:
            # Check if this is an addition operation with errors
            if not item["is_correct"] and "+" in item.get("operation", ""):
                patterns["addition_errors"] = True
            
            # Analyze step feedback for patterns
            for step in item.get("step_feedback", []):
                step_op = step.get("operation", "")
                
                # Check for sequence errors (one step not continuing from previous)
                if not step["is_correct"] and "should be" in step_op:
                    patterns["step_sequence_errors"] = True
                
                # Check for final result not matching last step
                if not step["is_correct"] and "Final result" in step_op:
                    patterns["final_result_mismatch"] = True
                
                # Check for potential rounding errors 
                # (very small differences between expected and actual)
                if not step["is_correct"] and step.get("expected") and step.get("actual"):
                    try:
                        expected = float(step["expected"])
                        actual = float(step["actual"])
                        if abs(expected - actual) < 0.01 and abs(expected - actual) > 0:
                            patterns["rounding_errors"] = True
                    except (ValueError, TypeError):
                        pass
        
        return patterns 