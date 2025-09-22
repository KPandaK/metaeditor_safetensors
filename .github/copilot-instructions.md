# MetaEditor SafeTensors - GitHub Copilot Instructions

MetaEditor SafeTensors is a Python GUI application for viewing and editing metadata in `.safetensors` files used in AI/ML model storage. The application is built with PySide6 (Qt for Python) and follows MVC architecture patterns.

## Code Standards

### Required Before Each Commit
- run `just fmt` before committing any changes to ensure proper code formatting
- This will run `ruff` in format mode to auto-fix formatting issues

### Development Flow
- Compile: `just compile` (compiles Qt resources, required to run the app)
- Test: `just test` (runs the full test suite)
- Full presubmit: `just presub` (runs formatting, linting, and tests)

### Repository Layout
```
.
├── assets/                          # Qt resource files (icons, stylesheets)
├── tests/                          # Unit test suite
├── metaeditor_safetensors/         # Main source code
│   ├── controllers/                # MVC controllers
│   ├── models/                     # Data models
│   ├── views/                      # GUI views
│   ├── services/                   # Business logic services
│   └── widgets/                    # Custom Qt widgets
├── justfile                        # Just task runner config (like Makefile)
├── pyproject.toml                  # Python project configuration
├── resources.qrc                   # Qt resource compilation manifest
├── main.py                         # Application entry point
└── run.sh / run.bat               # Platform-specific run scripts
```

### Key Guidelines
1. Follow best practices for Python and idiomatic patterns
2. Maintain existing code structure and organization
3. Use dependency injection patterns where appropriate
4. Write unit tests for new features and bug fixes
5. Do not manually edit generated files (`resources_rc.py`)

### Additional Notes
- **PySide6 tests fail on headless systems**: Use `QT_QPA_PLATFORM=offscreen`
- **Some tests require GUI**: CI uses `xvfb-run` on Linux for virtual display
- **virtual environments**: You do not need a virtual environment, all dependencies should be pre-installed before you get to work.