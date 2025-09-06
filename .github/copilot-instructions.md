# MetaEditor SafeTensors - GitHub Copilot Instructions

MetaEditor SafeTensors is a Python GUI application for viewing and editing metadata in `.safetensors` files used in AI/ML model storage. The application is built with PySide6 (Qt for Python) and follows MVC architecture patterns.

**ALWAYS reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working with Limited Dependencies

### If Unable to Install All Dependencies
If network issues prevent full dependency installation, you can still work effectively:

1. **Config service tests always work**:
   ```bash
   python -m unittest tests.test_config_service -v
   ```

2. **Code analysis without PySide6**:
   - View and edit Python source files
   - Analyze project structure and architecture
   - Review configuration files and documentation

3. **When dependencies are available**:
   - Always run full test suite and quality checks
   - Test GUI functionality thoroughly
   - Validate Qt resource compilation

### Partial Environment Setup
```bash
# Minimal setup for code analysis
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install --upgrade pip

# Try installing what you can
pip install coverage || echo "Coverage install failed"
pip install mypy || echo "MyPy install failed"
pip install ruff || echo "Ruff install failed"
```

## Working Effectively

### Initial Setup and Build
Set up the development environment and build the application:

1. **Check Python version** (requires Python 3.10+):
   ```bash
   python --version  # Must be 3.10 or higher
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate.bat  # Windows
   ```

3. **Install dependencies** - NEVER CANCEL: Takes 5-10 minutes. Set timeout to 15+ minutes:
   ```bash
   python -m pip install --upgrade pip
   pip install -e .[dev]
   ```
   
   **If installation fails with network timeouts:**
   - Try: `pip install -e .[dev] --timeout=120`
   - If persistent failures, install core dependencies individually:
     ```bash
     pip install PySide6 numpy safetensors coverage mypy ruff bandit
     ```

4. **Compile Qt resources and UI files** - Required before running:
   ```bash
   # Install Just task runner first (if available)
   just compile
   # OR manually compile if Just is not available:
   pyside6-rcc resources.qrc -o metaeditor_safetensors/resources_rc.py
   pyside6-uic designer/main_view.ui -o metaeditor_safetensors/views/main_view_ui.py
   pyside6-uic designer/about_dialog.ui -o metaeditor_safetensors/views/about_dialog_ui.py
   pyside6-uic designer/thumbnail_dialog.ui -o metaeditor_safetensors/views/thumbnail_dialog_ui.py
   ```

### Running the Application

1. **Run with Just task runner** (preferred):
   ```bash
   just run  # Automatically compiles Qt files first
   ```

2. **Run manually** (if Just is not available):
   ```bash
   # Ensure Qt files are compiled first
   python main.py
   ```

3. **Quick run scripts** (platform-specific):
   ```bash
   ./run.sh      # Linux/macOS
   run.bat       # Windows
   ```

### Testing

1. **Run all tests** - NEVER CANCEL: Takes 2-5 minutes. Set timeout to 10+ minutes:
   ```bash
   just test
   # OR manually:
   python -m coverage run -m unittest discover tests -v
   ```

2. **Run specific test module**:
   ```bash
   python -m unittest tests.test_config_service -v
   ```

3. **Run with GUI support** (for PySide6 tests):
   ```bash
   QT_QPA_PLATFORM=offscreen python -m unittest discover tests -v
   ```

### Code Quality and Validation

**ALWAYS run these before committing** - the CI will fail without them:

1. **Format code**:
   ```bash
   just fmt
   # OR manually:
   python -m ruff format --check --diff .
   ```

2. **Lint code**:
   ```bash
   just lint
   # OR manually:
   python -m ruff check --fix .
   ```

3. **Type checking**:
   ```bash
   just mypy
   # OR manually:
   python -m mypy .
   ```

4. **Security scanning**:
   ```bash
   just bandit
   # OR manually:
   python -m bandit -r metaeditor_safetensors/ -ll
   ```

5. **Run all presubmit checks** - NEVER CANCEL: Takes 3-8 minutes. Set timeout to 15+ minutes:
   ```bash
   just presub
   ```

## Validation Scenarios

After making any changes, ALWAYS validate functionality by:

### Basic Application Validation
1. **Start the application** and verify it opens without errors
2. **Open a sample safetensors file** (if available) or create a test file
3. **View metadata** - check that existing metadata displays correctly
4. **Edit metadata** - try adding, modifying, and removing metadata entries  
5. **Save changes** - ensure changes persist correctly

### Testing Without Real Files
If no safetensors files are available:
1. Start the application and verify the GUI loads
2. Check that menus and dialogs open correctly
3. Verify error handling for missing files

### Code Changes Validation
1. **Build succeeds**: `just compile` completes without errors
2. **Tests pass**: `just test` completes successfully
3. **Quality checks pass**: `just presub` completes without issues
4. **Application runs**: Basic GUI functionality works

## Timing Expectations

**CRITICAL: NEVER CANCEL these operations prematurely**

- **Dependency installation**: 5-10 minutes (set timeout: 15+ minutes)
- **Qt compilation**: 30 seconds - 2 minutes (usually fast)
- **Full test suite**: 2-5 minutes (set timeout: 10+ minutes)
- **All presubmit checks**: 3-8 minutes (set timeout: 15+ minutes)
- **Application startup**: 2-10 seconds
- **CI pipeline**: 10-20 minutes total across all platforms

## Project Structure and Key Files

### Repository Layout
```
.
├── .github/workflows/ci.yml         # GitHub Actions CI pipeline
├── assets/                          # Qt resource files (icons, stylesheets)
├── designer/                        # Qt Designer UI files (*.ui)
├── tests/                          # Unit test suite
├── metaeditor_safetensors/         # Main source code
│   ├── controllers/                # MVC controllers
│   ├── models/                     # Data models
│   ├── views/                      # GUI views (*_ui.py generated from *.ui)
│   ├── services/                   # Business logic services
│   └── widgets/                    # Custom Qt widgets
├── justfile                        # Just task runner config (like Makefile)
├── pyproject.toml                  # Python project configuration
├── resources.qrc                   # Qt resource compilation manifest
├── main.py                         # Application entry point
└── run.sh / run.bat               # Platform-specific run scripts
```

### Important Generated Files
- `metaeditor_safetensors/resources_rc.py` - Generated from resources.qrc
- `metaeditor_safetensors/views/*_ui.py` - Generated from designer/*.ui files

**DO NOT manually edit generated files** - they will be overwritten during compilation.

### Configuration Files
- `.env.development` - Environment variables for development
- `pyproject.toml` - Python dependencies and tool configuration  
- `.github/workflows/ci.yml` - CI/CD pipeline configuration

## Development Workflow

### Making Code Changes
1. **Always compile Qt files first**: `just compile` or manual pyside6-rcc/pyside6-uic commands
2. **Run relevant tests**: Target the specific area you're changing
3. **Run quality checks**: `just fmt && just lint && just mypy`
4. **Test application**: Verify your changes work in the GUI
5. **Run full validation**: `just presub` before committing

### Common File Relationships
- After editing `designer/*.ui` files → run `just compile` to regenerate `*_ui.py`
- After editing `assets/*` files → run `just compile` to regenerate `resources_rc.py`
- After editing service classes → run related tests in `tests/test_*_service.py`
- Always check `metaeditor_safetensors/app.py` - main application setup and dependency injection

### CI/CD Pipeline
The GitHub Actions CI pipeline (.github/workflows/ci.yml):
- Runs on Ubuntu, macOS, and Windows
- Tests Python versions 3.10, 3.11, 3.12
- Performs linting, type checking, and testing
- Generates coverage reports
- **Takes 10-20 minutes total** - DO NOT cancel jobs prematurely

## Common Issues and Solutions

### Build Issues
- **Missing pyside6-rcc/pyside6-uic**: Install with `pip install PySide6`
- **Qt compilation fails**: Check that .ui files in designer/ are valid Qt Designer files
- **Import errors**: Ensure virtual environment is activated and dependencies installed

### Test Issues  
- **PySide6 tests fail on headless systems**: Use `QT_QPA_PLATFORM=offscreen`
- **Some tests require GUI**: CI uses `xvfb-run` on Linux for virtual display

### Runtime Issues
- **Application won't start**: Check Python version (3.10+ required)
- **Missing resources**: Run `just compile` to regenerate resource files
- **Style issues**: Check `assets/style.qss` and resource compilation

### Network/Installation Issues
- **pip timeouts**: Try `pip install --timeout=120` or `pip install -e .[dev] --timeout=300`
- **Dependency installation fails**: Install core packages individually: `pip install PySide6 numpy safetensors`
- **Missing system dependencies on Linux**: Install Qt system libraries as shown in CI:
  ```bash
  sudo apt-get install -y libegl1 libegl-mesa0 libxkbcommon-x11-0 libxcb-icccm4 \
    libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
    libxcb-xinerama0 libfontconfig1 libxrender1 libxss1 libglib2.0-0
  ```

## Key Services and Components

### Core Services (in metaeditor_safetensors/services/)
- `SafetensorsService` - Handles .safetensors file I/O and metadata operations
- `ConfigService` - Manages application settings and recent files
- `StylesheetService` - Handles Qt stylesheet loading and live reload (dev mode)
- `ImageService` - Image processing and thumbnail generation

### MVC Architecture
- **Models** (`models/`) - Data structures and business logic
- **Views** (`views/`) - Qt GUI components and generated UI files
- **Controllers** (`controllers/`) - Coordinates between models and views

**When changing business logic**: Focus on services and models
**When changing UI**: Edit designer/*.ui files, then recompile
**When changing application behavior**: Check controllers for coordination logic

## Summary

This document provides comprehensive instructions for GitHub Copilot agents working on the MetaEditor SafeTensors codebase. Key points:

- **Python Qt GUI application** - Uses PySide6, requires Python 3.10+
- **Build system**: Just task runner (fallback to manual commands documented)
- **Test suite**: Comprehensive unittest coverage, some tests work without full dependencies
- **Code quality**: Ruff (linting/formatting), MyPy (typing), Bandit (security)
- **CI/CD**: Multi-platform GitHub Actions pipeline
- **Key timing**: Dependencies 5-10min, tests 2-5min, presubmit 3-8min - NEVER CANCEL

**Always validate changes through multiple channels**: build success, tests passing, code quality checks, and actual application functionality when possible. The instructions are designed to be copy-pasteable and work reliably for any developer with a fresh repository clone.