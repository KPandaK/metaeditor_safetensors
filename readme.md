# MetaEditor Safetensors

A lightweight Python tool and GUI for inspecting and editing `.safetensors` files, commonly used in AI and ML model storage.

## Features
- View and edit metadata in safetensors files
- Implements the [Stability AI ModelSpec](https://github.com/Stability-AI/ModelSpec) version 1.0.1 for standardized metadata.
- Simple GUI usage

## Installation

1. **Clone the repository:**
  ```sh
  git clone <your-repo-url>
  cd metaeditor_safetensors
  ```

2. **(Optional) Create a virtual environment:**
  ```sh
  python -m venv venv
  venv\Scripts\activate  # Windows
  ```

3. **Install dependencies:**
  ```sh
  pip install -r requirements.txt
  ```

## Usage
Run the main application:
```sh
python src/metaeditor_safetensors/main.py
```
Use the GUI for interactive editing.

## License
MIT License


TODO:

- Version handling

##User Experience Enhancements
- Implement drag-and-drop file support
- Add recent files menu
- Better error messages with recovery suggestions

#Feature Additions
##Metadata Validation & Enhancement
- Add more comprehensive validation rules
- Support for custom metadata fields
- Metadata templates for common model types
- Import/export metadata to JSON

##Image Management
- Support for multiple thumbnail formats
- Batch image processing
- Image preview improvements
- Automatic thumbnail generation from model outputs

##File Management
- Batch processing of multiple safetensors files
- Compare metadata between files
- Merge/split safetensors files
- Convert between different model formats
#Code Quality & Maintenance
##Testing & Documentation
- Add more comprehensive test coverage
- Create user documentation/help system
- Add type hints throughout the codebase
- Set up automated testing pipeline
- fixup existing tests and ensure better test coverage