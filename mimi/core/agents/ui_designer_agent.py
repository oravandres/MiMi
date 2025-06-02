import logging
from pathlib import Path
from ..agents.base_agent import Agent

class UIDesignerAgent(Agent):
    """
    UI/UX Designer Agent for creating UI/UX designs and specifications.
    """
    
    def execute(self, input_data):
        """
        Execute the UI/UX designer agent.

        Args:
            input_data: Input data containing project requirements, path, etc.

        Returns:
            dict: Result of the execution
        """
        try:
            project_dir = input_data['project_dir']
            
            # Extract requirements from input data
            requirements = self._extract_requirements(input_data)
            
            # Create UI/UX design
            ui_design = self._create_ui_design(requirements)
            
            # Write UI/UX design to file
            self.write_log_to_file(
                project_dir=project_dir,
                content=ui_design,
                subfolder="docs",
                filename="ui_design.md"
            )
            
            # Log this action to the project log
            self.log_to_agent_file(
                project_dir=project_dir,
                action_type="ui-design",
                input_summary=f"Project requirements for UI/UX design",
                output_summary=f"Generated UI/UX design specification",
                details={
                    "ui_file": "docs/ui_design.md",
                    "agent_role": self.role
                }
            )
            
            # Return success
            return {
                "success": True,
                "message": f"{self.name} successfully created UI/UX design",
                "ui_design": ui_design
            }
        except Exception as e:
            logging.error(f"{self.name} execution failed: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "ui_design": None
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
        logging.debug("Input data:")
        logging.debug("=" * 50)
        logging.debug(f"{input_data}")
        logging.debug("=" * 50)
        if isinstance(input_data, dict):
            if 'input' in input_data:
                if isinstance(input_data['input'], dict) and 'input' in input_data['input']:
                    return input_data['input']['input']
                return str(input_data['input'])
            return str(input_data)
        return str(input_data)
    
    def _create_ui_design(self, requirements):
        """
        Create UI/UX design based on requirements.
        
        Args:
            requirements: Project requirements
            
        Returns:
            str: UI/UX design in markdown format
        """
        # For demonstration, generate a generic UI/UX design
        return """# UI/UX Design Specification for Flappy Bird Game

## Overview
This document outlines the UI/UX design for a Flappy Bird game implemented as a single HTML file with JavaScript.

## Color Palette
| Element | Color | Hex Code |
|---------|-------|----------|
| Background (Sky) | Light Blue | #70c5ce |
| Ground | Sandy Brown | #dec387 |
| Pipes | Green | #74c842 |
| Bird | Yellow | #f8bc34 |
| Buttons | Orange | #f1a814 |
| Text | White | #ffffff |

## Typography
- **Game Title**: 'Press Start 2P', cursive, 32px
- **Score Display**: 'Press Start 2P', cursive, 24px
- **Button Text**: Arial, sans-serif, 16px
- **Instructions**: Arial, sans-serif, 14px

## Layout
1. **Game Canvas**: 320px × 480px centered in viewport
2. **Score Display**: Top-left corner of canvas
3. **Start Screen**: Centered overlay with title, instructions, and start button
4. **Game Over Screen**: Centered overlay with score, high score, and restart button

## User Flow
1. **Initial State**: Player sees start screen with game title and start button
2. **Game Play**: Player taps/clicks or presses space to make bird flap
3. **Game Over**: On collision, show game over screen with score and restart option

## Responsive Design
- **Mobile**: Canvas scales to fit viewport width while maintaining aspect ratio
- **Desktop**: Canvas fixed size centered in viewport

## Animations
1. **Bird Animation**: Gentle bob up and down on start screen
2. **Flap Animation**: Quick upward movement followed by gravity fall
3. **Game Over Animation**: Bird falls, screen flashes red briefly

## Accessibility
- **Color Contrast**: All text has contrast ratio of at least 4.5:1
- **Keyboard Navigation**: Game playable with keyboard (space bar)
- **Instructions**: Clear, concise instructions visible on start screen

## Mockup Screens
(ASCII art representation of screens)

```
Start Screen:
┌────────────────────┐
│     FLAPPY BIRD    │
│                    │
│       [Bird]       │
│                    │
│ Click or press     │
│ Space to flap      │
│                    │
│    [Start Game]    │
└────────────────────┘

Game Screen:
┌────────────────────┐
│ Score: 5           │
│                    │
│     [Bird]         │
│           ┌─┐      │
│           │ │      │
│           │ │      │
│     ┌─┐   └─┘      │
│     │ │            │
└─────┴─┴────────────┘

Game Over Screen:
┌────────────────────┐
│     GAME OVER      │
│                    │
│    Your Score: 5   │
│    High Score: 10  │
│                    │
│     [Play Again]   │
└────────────────────┘
```

This design emphasizes simplicity, clarity, and an engaging user experience while maintaining the classic Flappy Bird feel that players know and love.""" 