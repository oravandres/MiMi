#!/usr/bin/env python3
"""
Simple MiMi Desktop App - For Testing PySide6
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel

# Add MiMi to path if it's not already there
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

# Import MiMi modules
try:
    from mimi.utils import ensure_project_directory_exists
except ImportError:
    print("MiMi framework not found. Make sure you're running from the MiMi directory.")

class SimpleApp(QMainWindow):
    """A simple test application to check if PySide6 is working."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PySide6 Test")
        self.setMinimumSize(400, 300)
        
        # Ensure projects directory exists
        self.projects_dir = ensure_project_directory_exists()
        
        # Main widget and layout
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # Add a label
        label = QLabel("PySide6 is working!")
        label.setStyleSheet("font-size: 24px;")
        layout.addWidget(label)
        
        # Add a button
        button = QPushButton("Click Me")
        button.clicked.connect(self.on_button_clicked)
        layout.addWidget(button)
        
        # Set central widget
        self.setCentralWidget(main_widget)
    
    def on_button_clicked(self):
        """Handle button click."""
        print("Button clicked!")

if __name__ == "__main__":
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = SimpleApp()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec_()) 