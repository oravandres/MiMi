import logging
from pathlib import Path
from ..agents.base_agent import Agent

class DeveloperAgent(Agent):
    """
    Developer Agent for implementing code.
    """
    
    def execute(self, input_data):
        """
        Execute the developer agent.

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

            # Extract requirements
            requirements = self._extract_requirements(input_data)
            
            # Generate implementation
            implementation = self._generate_implementation(requirements)
            
            # Write logs to file
            agent_type = getattr(self, 'role', 'developer').lower()
            log_filename = f"{agent_type}_implementation.md"
            self.write_log_to_file(
                project_dir=project_dir,
                content=implementation,
                subfolder="src",
                filename=log_filename
            )
            
            # Log this action to the project log
            self.log_to_agent_file(
                project_dir=project_dir,
                action_type="implementation",
                input_summary=f"Project requirements for implementation",
                output_summary=f"Generated {agent_type} implementation",
                details={
                    "implementation_file": f"src/{log_filename}",
                    "agent_role": self.role
                }
            )
            
            # Implement actual code files
            self._implement_code_files(project_dir, implementation)
            
            # Return success
            return {
                "success": True,
                "message": f"{self.name} successfully generated implementation",
                "implementation": implementation
            }
        except Exception as e:
            logging.error(f"{self.name} execution failed: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "implementation": None
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
    
    def _generate_implementation(self, requirements):
        """
        Generate implementation plan based on requirements.
        
        Args:
            requirements: Project requirements
            
        Returns:
            str: Implementation plan in markdown format
        """
        # For demonstration, generate a generic implementation plan
        return """# Implementation Plan for Flappy Bird Game

## Core Components

1. **HTML Structure**
   - Create basic HTML file with canvas element
   - Add score display and game control elements
   - Set up viewport meta tags for responsiveness

2. **CSS Styling**
   - Style game container and canvas
   - Style score display and game control buttons
   - Create responsive design rules

3. **JavaScript Game Logic**
   - Initialize game variables and constants
   - Implement bird mechanics (gravity, flap)
   - Create pipe generation and movement
   - Handle collision detection
   - Implement scoring system
   - Set up game states (start, play, game over)

## Implementation Details

### HTML Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flappy Bird</title>
    <style>
        /* CSS will be here */
    </style>
</head>
<body>
    <div class="game-container">
        <div class="score">Score: <span id="score">0</span></div>
        <canvas id="game-canvas" width="320" height="480"></canvas>
        <div class="start-screen" id="start-screen">
            <h1>Flappy Bird</h1>
            <button id="start-button">Start Game</button>
        </div>
        <div class="game-over" id="game-over">
            <h2>Game Over</h2>
            <p>Score: <span id="final-score">0</span></p>
            <p>High Score: <span id="high-score">0</span></p>
            <button id="restart-button">Play Again</button>
        </div>
    </div>
    <script>
        // JavaScript will be here
    </script>
</body>
</html>
```

### JavaScript Implementation
```javascript
// Game variables
const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');
const startScreen = document.getElementById('start-screen');
const gameOverScreen = document.getElementById('game-over');
const scoreDisplay = document.getElementById('score');
const finalScoreDisplay = document.getElementById('final-score');
const highScoreDisplay = document.getElementById('high-score');
const startButton = document.getElementById('start-button');
const restartButton = document.getElementById('restart-button');

// Game constants
const GRAVITY = 0.5;
const FLAP_FORCE = -8;
const PIPE_SPEED = 2;
const PIPE_SPAWN_INTERVAL = 1500;
const PIPE_GAP = 150;

// Game state
let gameActive = false;
let score = 0;
let highScore = localStorage.getItem('flappyHighScore') || 0;
highScoreDisplay.textContent = highScore;

// Bird object
const bird = {
    x: 50,
    y: canvas.height / 2,
    width: 30,
    height: 24,
    velocity: 0,
    
    draw: function() {
        ctx.fillStyle = '#f8bc34';
        ctx.fillRect(this.x, this.y, this.width, this.height);
    },
    
    flap: function() {
        if (gameActive) {
            this.velocity = FLAP_FORCE;
        }
    },
    
    update: function() {
        if (gameActive) {
            this.velocity += GRAVITY;
            this.y += this.velocity;
            
            // Check for collision with ground or ceiling
            if (this.y + this.height >= canvas.height - 50) {
                gameOver();
            }
            
            if (this.y <= 0) {
                this.y = 0;
                this.velocity = 0;
            }
        }
    }
};

// Pipes array
let pipes = [];

// Game functions
function startGame() {
    gameActive = true;
    score = 0;
    scoreDisplay.textContent = score;
    bird.y = canvas.height / 2;
    bird.velocity = 0;
    pipes = [];
    startScreen.style.display = 'none';
    gameOverScreen.style.display = 'none';
    
    // Start spawning pipes
    pipeInterval = setInterval(createPipe, PIPE_SPAWN_INTERVAL);
    
    // Start game loop
    requestAnimationFrame(gameLoop);
}

function gameOver() {
    gameActive = false;
    clearInterval(pipeInterval);
    
    // Update high score
    if (score > highScore) {
        highScore = score;
        localStorage.setItem('flappyHighScore', highScore);
        highScoreDisplay.textContent = highScore;
    }
    
    finalScoreDisplay.textContent = score;
    gameOverScreen.style.display = 'flex';
}

function createPipe() {
    if (!gameActive) return;
    
    const pipeHeight = Math.floor(Math.random() * (canvas.height - PIPE_GAP - 100)) + 50;
    
    pipes.push({
        x: canvas.width,
        y: 0,
        width: 50,
        height: pipeHeight,
        passed: false
    });
    
    pipes.push({
        x: canvas.width,
        y: pipeHeight + PIPE_GAP,
        width: 50,
        height: canvas.height - pipeHeight - PIPE_GAP,
        passed: false
    });
}

function updatePipes() {
    for (let i = 0; i < pipes.length; i++) {
        const pipe = pipes[i];
        pipe.x -= PIPE_SPEED;
        
        // Check for collision
        if (
            bird.x < pipe.x + pipe.width &&
            bird.x + bird.width > pipe.x &&
            bird.y < pipe.y + pipe.height &&
            bird.y + bird.height > pipe.y
        ) {
            gameOver();
        }
        
        // Check if pipe is passed
        if (!pipe.passed && pipe.x + pipe.width < bird.x) {
            pipe.passed = true;
            if (i % 2 === 0) { // Only count once per pipe pair
                score++;
                scoreDisplay.textContent = score;
            }
        }
    }
    
    // Remove off-screen pipes
    pipes = pipes.filter(pipe => pipe.x + pipe.width > 0);
}

function drawPipes() {
    ctx.fillStyle = '#74c842';
    pipes.forEach(pipe => {
        ctx.fillRect(pipe.x, pipe.y, pipe.width, pipe.height);
    });
}

function drawBackground() {
    // Sky
    ctx.fillStyle = '#70c5ce';
    ctx.fillRect(0, 0, canvas.width, canvas.height - 50);
    
    // Ground
    ctx.fillStyle = '#dec387';
    ctx.fillRect(0, canvas.height - 50, canvas.width, 50);
}

function gameLoop() {
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw background
    drawBackground();
    
    // Update and draw pipes
    if (gameActive) {
        updatePipes();
    }
    drawPipes();
    
    // Update and draw bird
    bird.update();
    bird.draw();
    
    // Continue game loop
    requestAnimationFrame(gameLoop);
}

// Event listeners
startButton.addEventListener('click', startGame);
restartButton.addEventListener('click', startGame);

document.addEventListener('keydown', function(e) {
    if (e.code === 'Space') {
        if (!gameActive && startScreen.style.display !== 'none') {
            startGame();
        } else {
            bird.flap();
        }
        e.preventDefault();
    }
});

canvas.addEventListener('click', function() {
    bird.flap();
});

// Initialize game
startScreen.style.display = 'flex';
gameOverScreen.style.display = 'none';
drawBackground();
bird.draw();
```

## Implementation Timeline
1. Set up basic HTML and CSS structure - 1 hour
2. Implement game mechanics and physics - 2 hours
3. Add pipe generation and collision detection - 2 hours
4. Implement scoring system and game states - 1 hour
5. Add visual polish and refinements - 1 hour
6. Testing and bug fixes - 1 hour

Total estimated time: 8 hours
"""
    
    def _implement_code_files(self, project_dir, implementation):
        """
        Implement actual code files based on the implementation plan.
        
        Args:
            project_dir: Project directory
            implementation: Implementation plan
        """
        try:
            # This would parse the implementation and create actual code files
            # For simplicity, we'll just create a placeholder file for now
            agent_type = getattr(self, 'role', 'developer').lower()
            
            # Different file types based on developer role
            if 'frontend' in agent_type:
                self.write_log_to_file(
                    project_dir=project_dir,
                    content="<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Flappy Bird</title>\n    <style>\n        /* Game styles */\n        body {\n            margin: 0;\n            padding: 0;\n            display: flex;\n            justify-content: center;\n            align-items: center;\n            height: 100vh;\n            background-color: #f0f0f0;\n            font-family: Arial, sans-serif;\n        }\n        \n        .game-container {\n            position: relative;\n            width: 320px;\n            height: 480px;\n        }\n        \n        #game-canvas {\n            border: 2px solid #000;\n            background-color: #70c5ce;\n        }\n        \n        .score {\n            position: absolute;\n            top: 10px;\n            left: 10px;\n            font-size: 24px;\n            font-weight: bold;\n            color: white;\n            z-index: 10;\n        }\n        \n        .start-screen, .game-over {\n            position: absolute;\n            top: 0;\n            left: 0;\n            width: 100%;\n            height: 100%;\n            display: flex;\n            flex-direction: column;\n            justify-content: center;\n            align-items: center;\n            background-color: rgba(0, 0, 0, 0.7);\n            color: white;\n            z-index: 20;\n        }\n        \n        button {\n            padding: 10px 20px;\n            font-size: 16px;\n            background-color: #f1a814;\n            color: white;\n            border: none;\n            border-radius: 5px;\n            cursor: pointer;\n            margin-top: 20px;\n        }\n        \n        button:hover {\n            background-color: #e09000;\n        }\n    </style>\n</head>\n<body>\n    <div class=\"game-container\">\n        <div class=\"score\">Score: <span id=\"score\">0</span></div>\n        <canvas id=\"game-canvas\" width=\"320\" height=\"480\"></canvas>\n        <div class=\"start-screen\" id=\"start-screen\">\n            <h1>Flappy Bird</h1>\n            <p>Click or press Space to flap</p>\n            <button id=\"start-button\">Start Game</button>\n        </div>\n        <div class=\"game-over\" id=\"game-over\">\n            <h2>Game Over</h2>\n            <p>Score: <span id=\"final-score\">0</span></p>\n            <p>High Score: <span id=\"high-score\">0</span></p>\n            <button id=\"restart-button\">Play Again</button>\n        </div>\n    </div>\n    \n    <script>\n        // Game variables\n        const canvas = document.getElementById('game-canvas');\n        const ctx = canvas.getContext('2d');\n        const startScreen = document.getElementById('start-screen');\n        const gameOverScreen = document.getElementById('game-over');\n        const scoreDisplay = document.getElementById('score');\n        const finalScoreDisplay = document.getElementById('final-score');\n        const highScoreDisplay = document.getElementById('high-score');\n        const startButton = document.getElementById('start-button');\n        const restartButton = document.getElementById('restart-button');\n\n        // Game constants\n        const GRAVITY = 0.5;\n        const FLAP_FORCE = -8;\n        const PIPE_SPEED = 2;\n        const PIPE_SPAWN_INTERVAL = 1500;\n        const PIPE_GAP = 150;\n\n        // Game state\n        let gameActive = false;\n        let score = 0;\n        let highScore = localStorage.getItem('flappyHighScore') || 0;\n        let pipeInterval;\n        highScoreDisplay.textContent = highScore;\n\n        // Bird object\n        const bird = {\n            x: 50,\n            y: canvas.height / 2,\n            width: 30,\n            height: 24,\n            velocity: 0,\n            \n            draw: function() {\n                ctx.fillStyle = '#f8bc34';\n                ctx.fillRect(this.x, this.y, this.width, this.height);\n            },\n            \n            flap: function() {\n                if (gameActive) {\n                    this.velocity = FLAP_FORCE;\n                }\n            },\n            \n            update: function() {\n                if (gameActive) {\n                    this.velocity += GRAVITY;\n                    this.y += this.velocity;\n                    \n                    // Check for collision with ground or ceiling\n                    if (this.y + this.height >= canvas.height - 50) {\n                        gameOver();\n                    }\n                    \n                    if (this.y <= 0) {\n                        this.y = 0;\n                        this.velocity = 0;\n                    }\n                }\n            }\n        };\n\n        // Pipes array\n        let pipes = [];\n\n        // Game functions\n        function startGame() {\n            gameActive = true;\n            score = 0;\n            scoreDisplay.textContent = score;\n            bird.y = canvas.height / 2;\n            bird.velocity = 0;\n            pipes = [];\n            startScreen.style.display = 'none';\n            gameOverScreen.style.display = 'none';\n            \n            // Start spawning pipes\n            pipeInterval = setInterval(createPipe, PIPE_SPAWN_INTERVAL);\n            \n            // Start game loop\n            requestAnimationFrame(gameLoop);\n        }\n\n        function gameOver() {\n            gameActive = false;\n            clearInterval(pipeInterval);\n            \n            // Update high score\n            if (score > highScore) {\n                highScore = score;\n                localStorage.setItem('flappyHighScore', highScore);\n                highScoreDisplay.textContent = highScore;\n            }\n            \n            finalScoreDisplay.textContent = score;\n            gameOverScreen.style.display = 'flex';\n        }\n\n        function createPipe() {\n            if (!gameActive) return;\n            \n            const pipeHeight = Math.floor(Math.random() * (canvas.height - PIPE_GAP - 100)) + 50;\n            \n            pipes.push({\n                x: canvas.width,\n                y: 0,\n                width: 50,\n                height: pipeHeight,\n                passed: false\n            });\n            \n            pipes.push({\n                x: canvas.width,\n                y: pipeHeight + PIPE_GAP,\n                width: 50,\n                height: canvas.height - pipeHeight - PIPE_GAP,\n                passed: false\n            });\n        }\n\n        function updatePipes() {\n            for (let i = 0; i < pipes.length; i++) {\n                const pipe = pipes[i];\n                pipe.x -= PIPE_SPEED;\n                \n                // Check for collision\n                if (\n                    bird.x < pipe.x + pipe.width &&\n                    bird.x + bird.width > pipe.x &&\n                    bird.y < pipe.y + pipe.height &&\n                    bird.y + bird.height > pipe.y\n                ) {\n                    gameOver();\n                }\n                \n                // Check if pipe is passed\n                if (!pipe.passed && pipe.x + pipe.width < bird.x) {\n                    pipe.passed = true;\n                    if (i % 2 === 0) { // Only count once per pipe pair\n                        score++;\n                        scoreDisplay.textContent = score;\n                    }\n                }\n            }\n            \n            // Remove off-screen pipes\n            pipes = pipes.filter(pipe => pipe.x + pipe.width > 0);\n        }\n\n        function drawPipes() {\n            ctx.fillStyle = '#74c842';\n            pipes.forEach(pipe => {\n                ctx.fillRect(pipe.x, pipe.y, pipe.width, pipe.height);\n            });\n        }\n\n        function drawBackground() {\n            // Sky\n            ctx.fillStyle = '#70c5ce';\n            ctx.fillRect(0, 0, canvas.width, canvas.height - 50);\n            \n            // Ground\n            ctx.fillStyle = '#dec387';\n            ctx.fillRect(0, canvas.height - 50, canvas.width, 50);\n        }\n\n        function gameLoop() {\n            // Clear canvas\n            ctx.clearRect(0, 0, canvas.width, canvas.height);\n            \n            // Draw background\n            drawBackground();\n            \n            // Update and draw pipes\n            if (gameActive) {\n                updatePipes();\n            }\n            drawPipes();\n            \n            // Update and draw bird\n            bird.update();\n            bird.draw();\n            \n            // Continue game loop\n            requestAnimationFrame(gameLoop);\n        }\n\n        // Event listeners\n        startButton.addEventListener('click', startGame);\n        restartButton.addEventListener('click', startGame);\n\n        document.addEventListener('keydown', function(e) {\n            if (e.code === 'Space') {\n                if (!gameActive && startScreen.style.display !== 'none') {\n                    startGame();\n                } else {\n                    bird.flap();\n                }\n                e.preventDefault();\n            }\n        });\n\n        canvas.addEventListener('click', function() {\n            bird.flap();\n        });\n\n        // Initialize game\n        startScreen.style.display = 'flex';\n        gameOverScreen.style.display = 'none';\n        drawBackground();\n        bird.draw();\n    </script>\n</body>\n</html>",
                    subfolder="src",
                    filename="index.html"
                )
                
                # Log this action to the project log
                self.log_to_agent_file(
                    project_dir=project_dir,
                    action_type="code-implementation",
                    input_summary=f"Implementation plan for frontend",
                    output_summary=f"Generated index.html with Flappy Bird game",
                    details={
                        "file": "src/index.html",
                        "agent_role": self.role
                    }
                )
            elif 'backend' in agent_type:
                self.write_log_to_file(
                    project_dir=project_dir,
                    content="// Generated backend code implementation\n\nconst express = require('express');\nconst app = express();\nconst PORT = process.env.PORT || 3000;\n\n// Serve static files\napp.use(express.static('public'));\n\n// API endpoint for high scores\napp.get('/api/highscores', (req, res) => {\n  res.json({ highScore: 100 });\n});\n\n// Start server\napp.listen(PORT, () => {\n  console.log(`Server running on port ${PORT}`);\n});",
                    subfolder="src",
                    filename="server.js"
                )
                
                # Log this action to the project log
                self.log_to_agent_file(
                    project_dir=project_dir,
                    action_type="code-implementation",
                    input_summary=f"Implementation plan for backend",
                    output_summary=f"Generated server.js with Express server",
                    details={
                        "file": "src/server.js",
                        "agent_role": self.role
                    }
                )
            elif 'database' in agent_type:
                self.write_log_to_file(
                    project_dir=project_dir,
                    content="// Generated database schema implementation\n\nconst mongoose = require('mongoose');\n\n// Define high score schema\nconst highScoreSchema = new mongoose.Schema({\n  player: { type: String, required: true },\n  score: { type: Number, required: true },\n  date: { type: Date, default: Date.now }\n});\n\n// Create model\nconst HighScore = mongoose.model('HighScore', highScoreSchema);\n\nmodule.exports = HighScore;",
                    subfolder="src",
                    filename="schema.js"
                )
                
                # Log this action to the project log
                self.log_to_agent_file(
                    project_dir=project_dir,
                    action_type="code-implementation",
                    input_summary=f"Implementation plan for database",
                    output_summary=f"Generated schema.js with Mongoose schema",
                    details={
                        "file": "src/schema.js",
                        "agent_role": self.role
                    }
                )
        except Exception as e:
            logging.error(f"Failed to implement code files: {str(e)}")
            # We'll continue even if this fails 