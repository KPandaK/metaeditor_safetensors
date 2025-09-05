#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Pre-submission script for metaeditor_safetensors
    
.DESCRIPTION
    Runs all quality checks, formatting, and tests before submitting code.
    This script ensures code meets quality standards and all tests pass.
    
.PARAMETER Fix
    Automatically fix issues where possible (formatting, imports, etc.)
    
.PARAMETER SkipSecurity
    Skip security scanning (useful for development)
    
.PARAMETER SkipTests
    Skip running tests (useful for quick formatting checks)
    
.EXAMPLE
    .\scripts\pre_submit.ps1
    Run all checks without fixing issues
    
.EXAMPLE
    .\scripts\pre_submit.ps1 -Fix
    Run all checks and automatically fix formatting issues
    
.EXAMPLE
    .\scripts\pre_submit.ps1 -Fix -SkipSecurity
    Run checks with fixes but skip security scanning
#>

param(
    [switch]$Fix,
    [switch]$SkipSecurity,
    [switch]$SkipTests,
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output (using PowerShell native colors)
function Write-Status {
    param([string]$Message, [string]$Color = "White")
    Write-Host "==> $Message" -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-Host "$([char]0x2713) $Message" -ForegroundColor Green  # ✓
}

function Write-Error {
    param([string]$Message)
    Write-Host "$([char]0x2717) $Message" -ForegroundColor Red  # ✗
}

function Write-Warning {
    param([string]$Message)
    Write-Host "$([char]0x26A0) $Message" -ForegroundColor Yellow  # ⚠
}

function Test-Command {
    param([string]$Command)
    return $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# Change to project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

Write-Status "Starting pre-submission checks for metaeditor_safetensors" "Cyan"
Write-Host ""

# Check if we're in a virtual environment
if (-not $env:VIRTUAL_ENV) {
    Write-Warning "Virtual environment not detected. Attempting to activate..."
    if (Test-Path "venv/Scripts/Activate.ps1") {
        & "venv/Scripts/Activate.ps1"
        Write-Success "Virtual environment activated"
    } else {
        Write-Error "No virtual environment found. Please create and activate a virtual environment first."
        exit 1
    }
}

$exitCode = 0

# Step 1: Code Formatting and Quality
Write-Status "1. Running code formatting and quality checks" "Blue"

try {
    if ($Fix) {
        Write-Status "  Fixing formatting issues with Ruff..." "Cyan"
        python -m ruff check --fix . --unsafe-fixes
        if ($LASTEXITCODE -ne 0) { throw "Ruff fix failed" }
        Write-Success "  Code formatting fixed"
    } else {
        Write-Status "  Checking code formatting with Ruff..." "Cyan"
        python -m ruff check . --output-format=github
        if ($LASTEXITCODE -ne 0) { 
            Write-Error "  Code formatting issues found. Run with -Fix to automatically fix them."
            $exitCode = 1
        } else {
            Write-Success "  Code formatting is clean"
        }
    }
} catch {
    Write-Error "  Code formatting check failed: $_"
    $exitCode = 1
}

# Step 2: Type Checking
Write-Status "2. Running type checks" "Blue"

try {
    Write-Status "  Checking types with mypy..." "Cyan"
    python -m mypy metaeditor_safetensors/ --show-error-codes --no-error-summary
    if ($LASTEXITCODE -ne 0) { 
        Write-Error "  Type checking failed"
        $exitCode = 1
    } else {
        Write-Success "  Type checking passed"
    }
} catch {
    Write-Error "  Type checking failed: $_"
    $exitCode = 1
}

# Step 3: Security Scanning
if (-not $SkipSecurity) {
    Write-Status "3. Running security scans" "Blue"
    
    try {
        # Bandit security scan
        Write-Status "  Scanning for security issues with Bandit..." "Cyan"
        python -m bandit -r metaeditor_safetensors/ --severity-level medium --confidence-level medium
        if ($LASTEXITCODE -ne 0) { 
            Write-Error "  Security issues found"
            $exitCode = 1
        } else {
            Write-Success "  No security issues found"
        }
        
        # pip-audit dependency scan
        Write-Status "  Scanning dependencies with pip-audit..." "Cyan"
        python -m pip_audit --progress-spinner=off
        if ($LASTEXITCODE -ne 0) { 
            Write-Error "  Vulnerable dependencies found"
            $exitCode = 1
        } else {
            Write-Success "  No vulnerable dependencies found"
        }
    } catch {
        Write-Error "  Security scanning failed: $_"
        $exitCode = 1
    }
} else {
    Write-Status "3. Security scanning skipped" "Yellow"
}

# Step 4: Tests
if (-not $SkipTests) {
    Write-Status "4. Running tests" "Blue"
    
    try {
        Write-Status "  Running unit tests..." "Cyan"
        if ($Verbose) {
            python -m unittest discover tests -v
        } else {
            python -m unittest discover tests
        }
        if ($LASTEXITCODE -ne 0) { 
            Write-Error "  Tests failed"
            $exitCode = 1
        } else {
            Write-Success "  All tests passed"
        }
        
        # Coverage report (optional)
        if (Test-Command "coverage") {
            Write-Status "  Generating coverage report..." "Cyan"
            coverage run -m unittest discover tests
            coverage report --show-missing --skip-covered
            Write-Success "  Coverage report generated"
        }
    } catch {
        Write-Error "  Tests failed: $_"
        $exitCode = 1
    }
} else {
    Write-Status "4. Tests skipped" "Yellow"
}

# Summary
Write-Host ""
Write-Status "Pre-submission check summary" "Cyan"

if ($exitCode -eq 0) {
    Write-Success "All checks passed! Code is ready for submission."
    Write-Host ""
    Write-Status "Next steps:" "Cyan"
    Write-Host "  1. Review your changes: git diff"
    Write-Host "  2. Stage your changes: git add ."
    Write-Host "  3. Commit your changes: git commit -m 'Your message'"
    Write-Host "  4. Push your changes: git push"
} else {
    Write-Error "Some checks failed. Please fix the issues before submitting."
    Write-Host ""
    Write-Status "Common fixes:" "Cyan"
    Write-Host "  $([char]0x2022) Run with -Fix to automatically fix formatting"
    Write-Host "  $([char]0x2022) Check type hints in flagged files"
    Write-Host "  $([char]0x2022) Review and fix failing tests"
    Write-Host "  $([char]0x2022) Address security findings if any"
}

exit $exitCode
