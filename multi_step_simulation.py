#!/usr/bin/env python3
"""Simulation of the multi-step workflow where each agent performs multiple additions."""

class Agent:
    """Base agent class."""
    
    def __init__(self, name, role, description):
        self.name = name
        self.role = role
        self.description = description
        
    def log(self, action, message):
        print(f"[{self.name}] {action}: {message}")
        
    def execute(self, task_input):
        """Execute method to be overridden."""
        self.log("execute", f"Processing input: {task_input}")
        return task_input


class NumberAdderAgent(Agent):
    """Agent that adds a specific number to the input multiple times."""
    
    def __init__(self, name, role, description, number_to_add, repetitions=1):
        super().__init__(name, role, description)
        self.number_to_add = number_to_add
        self.repetitions = repetitions
        
    def execute(self, task_input):
        """Add the specified number to the input multiple times."""
        if isinstance(task_input, dict) and "input" in task_input:
            input_value = task_input["input"]
        else:
            input_value = task_input
            
        self.log("execute", f"Adding {self.number_to_add} to {input_value} {self.repetitions} times")
        
        # Calculate the total addition and track steps
        total_to_add = self.number_to_add * self.repetitions
        result = input_value + total_to_add
        
        # Track each step
        steps = []
        current_value = input_value
        for i in range(self.repetitions):
            current_value += self.number_to_add
            steps.append({
                "step": i + 1,
                "value_before": current_value - self.number_to_add,
                "value_after": current_value,
                "added": self.number_to_add
            })
        
        # For simulation, we'll introduce an error in one agent
        if self.name == "agent-buggy" and self.repetitions > 1:
            # Introduce an error in step 3
            steps[2]["value_after"] += 1
            result += 1
            self.log("execute", f"Introduced a calculation error in step 3")
        
        self.log("execute", f"Final result after {self.repetitions} steps: {result}")
        
        return {
            "result": result,
            "input_value": input_value,
            "number_added": self.number_to_add,
            "repetitions": self.repetitions,
            "total_added": total_to_add,
            "steps": steps
        }


class AnalystAgent(Agent):
    """Agent that analyzes and verifies number additions."""
    
    def execute(self, task_input):
        """Verify that the addition was performed correctly."""
        self.log("execute", f"Analyzing addition: {task_input}")
        
        result_keys = []
        for key in task_input:
            if key.startswith("result"):
                result_keys.append(key)
        
        if not result_keys:
            self.log("warning", "No result keys found")
            return {
                "status": "warning",
                "message": "No result keys found to verify",
                "data": task_input
            }
        
        # Get the most recent result
        latest_result_key = result_keys[-1]  # In simulation, we just use the last one
        result_data = task_input[latest_result_key]
        
        # For detailed results with steps
        input_value = result_data["input_value"]
        number_added = result_data["number_added"]
        repetitions = result_data["repetitions"]
        total_added = result_data["total_added"]
        reported_result = result_data["result"]
        steps = result_data["steps"]
        
        # Verify final result
        expected_result = input_value + total_added
        final_result_correct = abs(expected_result - reported_result) < 1e-6
        
        # Verify each step
        step_verification_results = []
        all_steps_correct = True
        
        current = input_value
        for i, step in enumerate(steps):
            step_number = step["step"]
            before = step["value_before"]
            after = step["value_after"]
            added = step["added"]
            
            # Check if this step's starting value matches the previous step's ending value
            if abs(before - current) > 1e-6:
                all_steps_correct = False
                step_verification_results.append({
                    "step": step_number,
                    "operation": f"Step {step_number}: {before} should be {current}",
                    "expected": current,
                    "actual": before,
                    "is_correct": False
                })
            
            # Check if the addition was performed correctly
            expected_after = before + added
            step_correct = abs(expected_after - after) < 1e-6
            if not step_correct:
                all_steps_correct = False
            
            step_verification_results.append({
                "step": step_number,
                "operation": f"Step {step_number}: {before} + {added}",
                "expected": expected_after,
                "actual": after,
                "is_correct": step_correct
            })
            
            current = after
        
        # Check if the final step result matches the reported final result
        if abs(current - reported_result) > 1e-6:
            all_steps_correct = False
            step_verification_results.append({
                "step": "final",
                "operation": "Final result should match last step",
                "expected": current,
                "actual": reported_result,
                "is_correct": False
            })
        
        # Overall verification result
        if final_result_correct and all_steps_correct:
            self.log("execute", f"Verified: {input_value} + ({number_added} × {repetitions}) = {reported_result}")
            return {
                "status": "success",
                "message": "All calculations verified successfully",
                "data": {
                    "input": input_value,
                    latest_result_key: result_data,
                },
                "verification_results": [{
                    "operation": f"{input_value} + ({number_added} × {repetitions})",
                    "expected": expected_result,
                    "actual": reported_result,
                    "is_correct": True,
                    "steps": step_verification_results
                }]
            }
        else:
            errors = []
            if not final_result_correct:
                errors.append(f"Final result {reported_result} should be {expected_result}")
            
            if not all_steps_correct:
                errors.append("One or more calculation steps are incorrect")
            
            error_message = f"Calculation errors: {', '.join(errors)}"
            self.log("error", error_message)
            
            # Log details of step errors
            for step_result in step_verification_results:
                if not step_result["is_correct"]:
                    self.log("error", f"Step error: {step_result['operation']}, Expected: {step_result['expected']}, Actual: {step_result['actual']}")
            
            return {
                "status": "error",
                "message": error_message,
                "data": {
                    "input": input_value,
                    latest_result_key: result_data,
                },
                "verification_results": [{
                    "operation": f"{input_value} + ({number_added} × {repetitions})",
                    "expected": expected_result,
                    "actual": reported_result,
                    "is_correct": final_result_correct,
                    "steps": step_verification_results
                }]
            }


class FeedbackProcessorAgent(Agent):
    """Agent that processes verification results and provides feedback."""
    
    def execute(self, task_input):
        """Process verification results and provide feedback."""
        self.log("execute", f"Processing verification results")
        
        verified_keys = []
        for key in task_input:
            if key.startswith("verified"):
                verified_keys.append(key)
        
        if not verified_keys:
            self.log("warning", "No verification results found")
            return {
                "status": "warning",
                "message": "No verification results to process",
                "continue": True
            }
        
        # Get the most recent verification
        latest_verified_key = verified_keys[-1]  # In simulation, we just use the last one
        verification_result = task_input[latest_verified_key]
        
        status = verification_result["status"]
        message = verification_result["message"]
        verification_data = verification_result.get("verification_results", [])
        
        if status == "success":
            # Get detailed information about the operation
            operation_summary = ""
            if verification_data:
                operation = verification_data[0].get("operation", "")
                if operation:
                    operation_summary = f" Verified operation: {operation}"
                    
                # If there are steps, include a summary
                steps = verification_data[0].get("steps", [])
                if steps:
                    step_count = len(steps)
                    operation_summary += f" ({step_count} steps verified)"
            
            self.log("feedback", f"All calculations are correct!{operation_summary}")
            return {
                "status": "success",
                "message": f"All calculations are correct!{operation_summary}",
                "continue": True
            }
        elif status == "error":
            # Gather all error details
            details = []
            
            for result in verification_data:
                operation = result.get("operation", "unknown")
                expected = result.get("expected", "unknown")
                actual = result.get("actual", "unknown")
                
                if operation:
                    details.append(f"Operation: {operation}, Expected: {expected}, Actual: {actual}")
                
                # Add details about any failed steps
                steps = result.get("steps", [])
                if steps:
                    failed_steps = [s for s in steps if not s.get("is_correct", True)]
                    for step in failed_steps:
                        step_op = step.get("operation", "")
                        step_expected = step.get("expected", "")
                        step_actual = step.get("actual", "")
                        details.append(f"  - {step_op}, Expected: {step_expected}, Actual: {step_actual}")
            
            error_details = "\n".join(details)
            feedback_message = f"Error detected: {message}"
            if details:
                feedback_message += f"\nDetails:\n{error_details}"
                feedback_message += "\nPlease check the calculations and try again."
            
            self.log("error", feedback_message)
            return {
                "status": "error",
                "message": feedback_message,
                "details": details,
                "continue": False
            }
        else:
            self.log("warning", f"Unknown status: {status}")
            return {
                "status": "warning",
                "message": f"Received unknown verification status: {status}",
                "continue": True
            }


class Task:
    """A task that can be executed by an agent."""
    
    def __init__(self, name, description, agent, input_key=None, output_key=None, depends_on=None):
        self.name = name
        self.description = description
        self.agent = agent
        self.input_key = input_key
        self.output_key = output_key
        self.depends_on = depends_on or []
        
    def execute(self, task_input):
        """Execute the task with the given input."""
        print(f"[Task {self.name}] Executing with input: {task_input}")
        
        # Extract specific input if input_key is provided
        if self.input_key and isinstance(task_input, dict) and self.input_key in task_input:
            task_input_value = task_input[self.input_key]
            print(f"[Task {self.name}] Using input from key '{self.input_key}': {task_input_value}")
        else:
            task_input_value = task_input
        
        # Execute the task with the agent
        result = self.agent.execute(task_input_value)
        
        # Store the result under output_key if specified
        if self.output_key and isinstance(task_input, dict):
            output_data = task_input.copy() if isinstance(task_input, dict) else {}
            output_data[self.output_key] = result
            print(f"[Task {self.name}] Stored result in output key '{self.output_key}'")
            return output_data
        else:
            return result


def run_workflow(initial_input):
    """Run the multi-step workflow with the given input."""
    print(f"\n=== Starting multi-step workflow with input {initial_input} ===\n")
    
    # Create agents
    agent1 = NumberAdderAgent("agent-1", "Number Adder (+1)", "Adds 1 to input 5 times", 1, 5)
    agent2 = NumberAdderAgent("agent-2", "Number Adder (+2)", "Adds 2 to input 5 times", 2, 5)
    agent3 = NumberAdderAgent("agent-buggy", "Number Adder (+3)", "Adds 3 to input 5 times with a bug", 3, 5)
    analyst = AnalystAgent("analyst", "Analyst", "Verifies calculations")
    feedback = FeedbackProcessorAgent("feedback", "Feedback", "Provides feedback")
    
    # Create tasks
    tasks = [
        Task("add-1", "Add 1 to input 5 times", agent1, "input", "result1"),
        Task("verify-1", "Verify addition of 1", analyst, None, "verified1"),
        Task("feedback-1", "Process verification results", feedback, "verified1", "feedback1"),
        
        Task("add-2", "Add 2 to input 5 times", agent2, "input", "result2"),
        Task("verify-2", "Verify addition of 2", analyst, None, "verified2"),
        Task("feedback-2", "Process verification results", feedback, "verified2", "feedback2"),
        
        Task("add-3", "Add 3 to input 5 times (with bug)", agent3, "input", "result3"),
        Task("verify-3", "Verify addition of 3", analyst, None, "verified3"),
        Task("feedback-3", "Process verification results", feedback, "verified3", "feedback3"),
    ]
    
    # Run the workflow
    data = {"input": initial_input}
    
    for i, task in enumerate(tasks):
        print(f"\n--- Step {i+1}: {task.name} - {task.description} ---")
        result = task.execute(data)
        
        if isinstance(result, dict):
            data = result
            
            # Check for error feedback and halt if needed
            if task.name.startswith("feedback") and result.get(task.output_key, {}).get("continue") is False:
                print(f"\n!!! Stopping workflow due to error in {task.name} !!!")
                feedback_msg = result.get(task.output_key, {}).get("message", "Unknown error")
                print(f"Feedback: {feedback_msg}")
                break
    
    print("\n=== Workflow completed ===\n")
    return data


if __name__ == "__main__":
    # Run the workflow with input 10
    final_result = run_workflow(10)
    
    # Display the final state
    print("Final state:")
    for key, value in final_result.items():
        if key.startswith("result"):
            if isinstance(value, dict) and "result" in value:
                print(f"  {key}: {value['result']}")
            else:
                print(f"  {key}: {value}")
    print() 