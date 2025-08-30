# MetaEditor Safetensors

A lightweight Python tool and GUI for inspecting and editing `.safetensors` files, commonly used in AI and ML model storage.

## Features
- View and edit metadata in safetensors files
- Detect duplicate keys and header issues
- GUI tooltips for user guidance
- Simple command-line and GUI usage

## Installation
1. Clone the repository:
  ```sh
  git clone <your-repo-url>
  cd metaeditor_safetensors
  ```
2. (Optional) Create a virtual environment:
  ```sh
  python -m venv venv
  venv\Scripts\activate  # Windows
  ```
3. Install dependencies:
  ```sh
  pip install -r requirements.txt
  ```

## Usage
- Run the main application:
  ```sh
  python main.py
  ```
- Use the GUI for interactive editing.

## File Structure
- `main.py` - Entry point
- `editor.py` - Core editing logic
- `config.py` - Configuration
- `gui_tooltips.py` - GUI tooltips
- `utils.py` - Utility functions
- `test/` - Example safetensors files for testing

## Contributing
Pull requests and issues are welcome!

## License
MIT License
