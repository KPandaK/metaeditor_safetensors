# MetaEditor Safetensors

MetaEditor Safetensors is a Python GUI application for editing metadata in `.safetensors` files (used for AI/ML model storage). It uses PySide6 (Qt) for the interface and implements the Stability AI ModelSpec version 1.0.1.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Setup
- **Requirements**: Python 3.10 or newer is required
- **Virtual Environment Setup**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate  # Linux/Mac
  # OR 
  venv\Scripts\activate     # Windows
  ```

- **Install Dependencies**:
  ```bash
  python -m pip install --upgrade pip
  pip install -e .[dev]
  ```
  - **TIMING**: Dependency installation typically takes 2-5 minutes. NEVER CANCEL. Set timeout to 10+ minutes.
  - **NETWORK ISSUES**: If pip install fails due to network timeouts, this is a known limitation in some environments. In such cases:
    - Basic Python functionality and core tests (config service) will work
    - Full application requires PySide6, numpy, safetensors packages
    - Code quality tools (ruff, mypy, bandit) require dev dependencies

### Qt Compilation
- **Compile Qt Resources and UI Files** (usually optional - pre-compiled files included):
  ```bash
  # If just is available:
  just compile
  
  # Manual compilation (if just not available):
  pyside6-rcc resources.qrc -o metaeditor_safetensors/resources_rc.py
  # For each .ui file in designer/:
  pyside6-uic --from-imports designer/main_view.ui -o metaeditor_safetensors/views/main_view_ui.py
  pyside6-uic --from-imports designer/about_dialog.ui -o metaeditor_safetensors/views/about_dialog_ui.py
  pyside6-uic --from-imports designer/thumbnail_dialog.ui -o metaeditor_safetensors/views/thumbnail_dialog_ui.py
  ```
  - **NOTE**: Pre-compiled files are already included in the repository:
    - `metaeditor_safetensors/resources_rc.py`
    - `metaeditor_safetensors/views/*_ui.py`
  - Only recompile if you modify `.ui` files in `designer/` or `resources.qrc`

### Build and Run
- **Build the application**:
  ```bash
  # With just (preferred):
  just compile && python main.py
  
  # Manual approach:
  # 1. Compile Qt files (see above)
  # 2. Run application:
  python main.py
  ```
  - **TIMING**: Qt compilation takes 10-30 seconds. NEVER CANCEL.
  - **Application startup**: Takes 3-10 seconds depending on system.

- **IMPORTANT**: The provided `run.sh` and `run.bat` scripts have incorrect paths and reference non-existent `requirements.txt`. DO NOT use them as-is. Instead:
  - Use `python main.py` directly from the repository root
  - Use `pip install -e .[dev]` instead of `pip install -r requirements.txt`

### Testing
- **Run unit tests**:
  ```bash
  # With just:
  just test
  
  # Manual:
  python -m coverage run -m unittest discover tests -v
  python -m coverage html  # Generate coverage report
  ```
  - **TIMING**: Test suite takes 10-20 seconds (validated). NEVER CANCEL. Set timeout to 60+ seconds.
  - **Environment**: Tests require `QT_QPA_PLATFORM=offscreen` for headless environments.
  - **Coverage**: HTML coverage report is generated in `htmlcov/` directory.
  - **NOTE**: Some tests require PySide6/numpy dependencies. Config service tests run without dependencies.

### Code Quality
- **Formatting**:
  ```bash
  # Check formatting:
  python -m ruff format --check --diff .
  
  # Fix formatting:
  python -m ruff format .
  ```

- **Linting**:
  ```bash
  # Check and fix issues:
  python -m ruff check --fix .
  ```

- **Type Checking**:
  ```bash
  python -m mypy .
  ```

- **Security Scanning**:
  ```bash
  python -m bandit -r metaeditor_safetensors/ -ll
  ```

- **Presubmit Checks** (run all quality checks):
  ```bash
  # With just:
  just presub
  
  # Manual:
  python -m ruff format --check --diff .
  python -m ruff check --fix .
  python -m mypy .
  python -m unittest discover tests -v
  ```
  - **TIMING**: Full presubmit takes 1-3 minutes. NEVER CANCEL. Set timeout to 5+ minutes.

## Validation

### Manual Testing Scenarios
After making code changes, ALWAYS test the application functionality:

1. **Basic Launch Test**:
   ```bash
   python main.py
   ```
   - Verify the main window opens without errors
   - Check that the interface renders correctly

2. **File Operations**:
   - Test opening a safetensors file (if available)
   - Test metadata viewing and editing
   - Test saving changes

3. **UI Components**:
   - Test menu functionality
   - Test dialog boxes (About, etc.)
   - Test file browser interactions

### CI Validation
The CI system (.github/workflows/ci.yml) will fail if:
- Code formatting doesn't match ruff standards
- Linting finds issues that can't be auto-fixed
- Type checking fails with mypy
- Any unit tests fail
- Code coverage drops significantly

Always run `just presub` or the manual presubmit commands before committing.

## Repository Structure

### Key Directories
- `metaeditor_safetensors/` - Main application source code
  - `controllers/` - Application logic controllers
  - `models/` - Data models and business logic
  - `services/` - Service layer (file I/O, configuration)
  - `views/` - UI components and dialogs  
  - `widgets/` - Custom Qt widgets
- `designer/` - Qt Designer UI files (.ui)
- `assets/` - Images, icons, stylesheets
- `tests/` - Unit tests
- `.github/workflows/` - CI/CD configuration

### Key Files
- `main.py` - Application entry point
- `pyproject.toml` - Project configuration and dependencies
- `justfile` - Task runner configuration (similar to Makefile)
- `run.sh` / `run.bat` - Convenience startup scripts
- `resources.qrc` - Qt resource configuration
- `.coveragerc` - Test coverage configuration

### Generated Files (do not edit directly)
- `metaeditor_safetensors/resources_rc.py` - Compiled Qt resources
- `metaeditor_safetensors/views/*_ui.py` - Compiled UI files

## Common Tasks

### Validated Commands (tested to work)
```bash
# Check Python version (works)
python3 --version
# Expected: Python 3.12.3

# Create virtual environment (works) 
python3 -m venv venv && source venv/bin/activate

# Run basic tests (works - ~0.12 seconds)
export QT_QPA_PLATFORM=offscreen
python -m unittest discover tests -v --failfast
# Expected: 18 tests run successfully, 3 fail due to missing dependencies

# List repository structure (works)
ls -la
# Expected: justfile, main.py, metaeditor_safetensors/, tests/, etc.
```

### Commands that require dependencies
```bash
# Full dependency install (may timeout)
pip install -e .[dev]

# Run main application (needs PySide6)
python main.py

# Code quality tools (need dev dependencies)  
python -m ruff check .
python -m mypy .
python -m bandit -r metaeditor_safetensors/
```

### Adding New UI Components
1. Design in Qt Designer, save as `.ui` file in `designer/`
2. Run `just compile` to generate Python UI code
3. Import and use the generated `*_ui.py` files

### Adding Dependencies
1. Edit `pyproject.toml` to add new dependencies
2. Run `pip install -e .[dev]` to install
3. Test and update requirements if needed

### Debugging
- Use `QT_QPA_PLATFORM=offscreen` for headless testing
- Check Qt resource compilation if assets aren't loading
- Use `python -m pdb main.py` for debugging

## Platform-Specific Notes

### Windows
- Use `run.bat` for easy startup
- PowerShell is used for some justfile commands
- Qt tools: `pyside6-rcc.exe`, `pyside6-uic.exe`

### Linux/macOS
- Use `run.sh` for easy startup  
- Make sure `run.sh` is executable: `chmod +x run.sh`
- Qt tools: `pyside6-rcc`, `pyside6-uic`

## Troubleshooting

### Dependency Installation Issues
If `pip install -e .[dev]` fails due to network timeouts:

1. **What still works**:
   ```bash
   # Basic Python functionality
   python -c "print('Basic test')"
   
   # Core unit tests (config service)  
   python -m unittest discover tests -v --failfast
   ```

2. **What requires dependencies**:
   - Main application: `python main.py` (needs PySide6)
   - Qt compilation: `just compile` (needs PySide6 tools)
   - Code quality: `ruff`, `mypy`, `bandit` (needs dev dependencies)
   - Full test suite (needs numpy, safetensors)

3. **Alternative approaches**:
   - Use system packages if available: `apt install python3-pyside6 python3-numpy`
   - Work with available functionality and document network limitations
   - Focus on core logic testing that works without external dependencies

### Path Issues in Scripts
The `run.sh` and `run.bat` scripts have incorrect paths:
- **Wrong**: `cd src/metaeditor_safetensors` 
- **Correct**: Work from repository root, run `python main.py`
- **Wrong**: `pip install -r requirements.txt`
- **Correct**: `pip install -e .[dev]`

## Known Limitations
- **Network Dependencies**: pip install may timeout in environments with limited network access. Use system packages if available.
- **Headless Environments**: Requires `QT_QPA_PLATFORM=offscreen` for testing without display.
- **Qt Tools**: PySide6 command-line tools must be available in PATH after pip install.
- **Run Scripts Issue**: The provided `run.sh` and `run.bat` scripts have incorrect paths (`src/metaeditor_safetensors` should be `.`) and reference non-existent `requirements.txt`. Use direct Python commands instead.
- **Partial Test Coverage**: Some tests require PySide6/numpy dependencies and will fail without them. Core tests (config service) run successfully without external dependencies.

## Development Workflow
1. Make code changes
2. Run `just compile` to update Qt files
3. Run `just presub` to check code quality
4. Test manually: `python main.py`
5. Run specific tests if needed
6. Commit changes

Always validate changes with both automated tests and manual application testing before committing.