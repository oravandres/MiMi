import logging
from pathlib import Path
from ..agents.base_agent import Agent

class TechnicalWriterAgent(Agent):
    """
    Technical Writer Agent for creating documentation.
    """
    
    def execute(self, input_data):
        """
        Execute the technical writer agent.

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
            
            # Create documentation
            documentation = self._create_documentation(requirements)
            readme = self._create_readme(requirements)
            
            # Write documentation to files
            self.write_log_to_file(
                project_dir=project_dir,
                content=documentation,
                subfolder="docs",
                filename="documentation.md"
            )
            
            self.write_log_to_file(
                project_dir=project_dir,
                content=readme,
                subfolder="",  # Root directory
                filename="README.md"
            )
            
            # Log this action to the project log
            self.log_to_agent_file(
                project_dir=project_dir,
                action_type="documentation",
                input_summary=f"Project requirements for documentation",
                output_summary=f"Generated documentation and README",
                details={
                    "doc_file": "docs/documentation.md",
                    "readme_file": "README.md",
                    "agent_role": self.role
                }
            )
            
            # Return success
            return {
                "success": True,
                "message": f"{self.name} successfully created documentation",
                "documentation": documentation,
                "readme": readme
            }
        except Exception as e:
            logging.error(f"{self.name} execution failed: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "documentation": None,
                "readme": None
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
    
    def _create_documentation(self, requirements):
        """
        Create comprehensive documentation based on requirements.
        
        Args:
            requirements: Project requirements
            
        Returns:
            str: Documentation in markdown format
        """
        # For demonstration, generate generic documentation
        return """# Flappy Bird Game Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Game Mechanics](#game-mechanics)
4. [Code Structure](#code-structure)
5. [Game Components](#game-components)
6. [Customization](#customization)
7. [Troubleshooting](#troubleshooting)

## Introduction
This document provides comprehensive documentation for the Flappy Bird game implementation. The game is built using HTML5 Canvas and JavaScript, contained in a single HTML file for easy deployment and distribution.

## Installation
No installation is required. Simply open the `index.html` file in any modern web browser to play the game.

### Supported Browsers
- Chrome 60+
- Firefox 60+
- Safari 12+
- Edge 80+

## Game Mechanics
Flappy Bird is a side-scrolling game where the player controls a bird, attempting to fly between columns of green pipes without hitting them. The game mechanics include:

1. **Bird Control**: The bird automatically falls due to gravity. The player can make the bird flap upward by:
   - Clicking/tapping the screen
   - Pressing the space bar

2. **Scoring**: The player earns one point each time the bird passes through a pair of pipes.

3. **Game Over**: The game ends when the bird collides with:
   - Any pipe
   - The ground
   - The top of the screen

4. **High Score**: The game saves the highest score achieved in the browser's localStorage.

## Code Structure
The code is organized into several components:

```
index.html
├── HTML Structure
├── CSS Styles
└── JavaScript
    ├── Game Variables
    ├── Bird Object
    ├── Pipe Management
    ├── Drawing Functions
    ├── Game Loop
    ├── Event Handlers
    └── Utility Functions
```

## Game Components

### HTML Structure
The game uses a minimal HTML structure:
- Canvas element for rendering
- Score display
- Start and game over screens with buttons

### Bird Object
The bird object manages:
- Position and velocity
- Collision detection
- Flapping mechanics
- Drawing the bird sprite

### Pipe Management
Pipes are managed through:
- Spawning new pipes at intervals
- Moving pipes across the screen
- Checking for collisions
- Removing off-screen pipes

### Game States
The game has three main states:
1. **Start Screen**: Initial screen with game title and start button
2. **Active Game**: Player is controlling the bird
3. **Game Over**: Bird has collided, displaying score and restart option

## Customization
The game can be customized by modifying:

### Visual Elements
- Colors in the CSS variables
- Bird and pipe sprites
- Background elements

### Game Parameters
- Gravity strength (GRAVITY constant)
- Flap force (FLAP_FORCE constant)
- Pipe speed (PIPE_SPEED constant)
- Pipe spawn interval (PIPE_SPAWN_INTERVAL constant)
- Pipe gap size (PIPE_GAP constant)

## Troubleshooting

### Common Issues
1. **Game Running Slowly**
   - Try closing other browser tabs/applications
   - Ensure your browser is up to date

2. **Controls Not Responding**
   - Click directly on the game canvas
   - Ensure your browser allows JavaScript execution

3. **Game Not Saving High Score**
   - Check that localStorage is enabled in your browser
   - Try clearing browser cache if issues persist"""
    
    def _create_readme(self, requirements):
        """
        Create README file based on requirements.
        
        Args:
            requirements: Project requirements
            
        Returns:
            str: README in markdown format
        """
        # For demonstration, generate a generic README
        return """# Flappy Bird Game

A simple implementation of the classic Flappy Bird game using HTML5 Canvas and JavaScript.

## Features

- Single HTML file implementation
- Easy to run in any modern browser
- Canvas-based rendering for smooth graphics
- Keyboard and mouse/touch controls
- Score tracking with high score persistence
- Responsive design for various screen sizes

## How to Play

1. Open `index.html` in your web browser
2. Click the "Start Game" button or press Space
3. Keep the bird flying by clicking/tapping or pressing Space
4. Avoid the pipes and try to achieve a high score

## Controls

- **Mouse Click/Tap**: Make the bird flap
- **Space Bar**: Make the bird flap

## Technologies Used

- HTML5
- CSS3
- JavaScript (ES6+)
- Canvas API

## Browser Support

The game works in all modern browsers that support HTML5 Canvas:
- Chrome 60+
- Firefox 60+
- Safari 12+
- Edge 80+

## Installation

No installation required. Simply download the repository and open `index.html` in a web browser.

```bash
# Clone the repository (if you have Git)
git clone https://github.com/yourusername/flappy-bird.git

# Navigate to the project directory
cd flappy-bird

# Open in browser (Linux/Mac)
open index.html

# Open in browser (Windows)
start index.html
```

## Development

Want to contribute? Feel free to fork the repository and submit pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Inspired by the original Flappy Bird game by Dong Nguyen
- Built as a learning project for HTML5 Canvas and JavaScript game development""" 