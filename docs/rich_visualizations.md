# Rich Visualizations for MiMi

This document explains the enhanced terminal visualizations for the MiMi framework, powered by the [Rich](https://github.com/Textualize/rich) library.

## Features

The new Rich-based visualizations offer several improvements over the standard terminal output:

1. **Color-coded messages** based on message type and severity
2. **Stylized panels** for task completion and important events
3. **Better structured output** for improved readability
4. **Progress indicators** for long-running tasks
5. **Beautiful tables** for result summaries
6. **Graceful fallback** to plain text for environments without Rich

## Screenshots

![MiMi Rich Visualization Demo](../assets/rich_demo.png)

## Usage

The enhanced visualizations are enabled by default when you run MiMi commands. No additional configuration is needed unless you want to disable them.

```bash
# Run MiMi with enhanced visualizations (default)
python -m mimi --config projects/advanced --description "Create a flappy bird game in html and javascript"

# Run MiMi without color (for CI/CD environments or terminals that don't support color)
python -m mimi --config projects/advanced --description "Create a flappy bird game in html and javascript" --no-color
```

## Benefits

1. **Improved Readability**: The color-coded output and structured panels make it easier to scan and understand what's happening.
2. **Better Progress Tracking**: Task completions are highlighted, and durations are clearly displayed.
3. **Enhanced Debugging**: Different message types (info, warning, error) are visually distinct, making it easier to spot issues.
4. **Cleaner Summary Statistics**: Project results and statistics are presented in a clean, structured table format.

## Implementation Details

The enhanced visualizations are implemented in the `mimi/utils/logger.py` module, which uses the Rich library to format and display messages. The main components are:

1. **Console Output**: Messages are formatted with appropriate colors and styles.
2. **Panels**: Task completions and project completions are shown in styled panels.
3. **Tables**: Summary statistics are displayed in structured tables.
4. **Graceful Fallback**: If Rich is not available, the system falls back to standard logging.

## Demo

To see a demonstration of the Rich visualizations:

```bash
python examples/rich_demo.py
```

This will run a simulated MiMi workflow that shows the various visualization features.

## Requirements

The Rich visualizations require the [Rich library](https://github.com/Textualize/rich) to be installed:

```bash
pip install rich>=13.4.2
```

This dependency is automatically installed when you install MiMi using pip or poetry.

## Customization

If you're developing with MiMi and want to customize the visualizations:

1. Import the logger module: `from mimi.utils.logger import setup_logger`
2. Configure the logger with your preferred settings: `setup_logger(log_level="DEBUG", use_rich=True)`
3. Use the specialized logging functions for structured output:
   - `agent_log(agent_name, action, message)`
   - `task_log(task_name, status, message)`
   - `project_log(project_name, status, message)`

## Troubleshooting

If you encounter issues with the visualizations:

1. **Colors not displaying**: Check if your terminal supports ANSI colors. Try running with `--no-color` flag.
2. **Broken layouts**: Some terminal emulators may not handle panel borders correctly. Try adjusting the terminal width.
3. **Missing Rich library**: Install the Rich library with `pip install rich`.

## Future Enhancements

Planned improvements for future releases:

1. **Live task progress tracking** with progress bars
2. **Interactive components** for monitoring and controlling task execution
3. **Web-based dashboard** alternative to terminal output
4. **Customizable themes** for different visual styles 