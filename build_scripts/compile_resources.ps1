# PowerShell script to compile Qt resource files
param(
    [string]$ResourceFile = "resources.qrc",
    [string]$OutputFile = "metaeditor_safetensors/resources_rc.py",
    [string]$RccPath = ""
)

function Find-QtRccPath {
    # Try to find via Python in PATH
    try {
        $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
        if ($pythonPath) {
            $scriptsDir = Join-Path (Split-Path (Split-Path $pythonPath -Parent) -Parent) "Scripts"
            $rccPath = Join-Path $scriptsDir "pyside6-rcc.exe"
            if (Test-Path $rccPath) {
                Write-Host "Found RCC via Python installation: $rccPath" -ForegroundColor Green
                return $rccPath
            }
        }
    } catch {
        Write-Host "Python not found in PATH" -ForegroundColor Yellow
    }
    
    # Try to find pyside6-rcc directly in PATH
    try {
        $rccPath = (Get-Command pyside6-rcc -ErrorAction SilentlyContinue).Source
        if ($rccPath) {
            Write-Host "Found RCC in PATH: $rccPath" -ForegroundColor Green
            return $rccPath
        }
    } catch {
        # Not in PATH
    }
    
    return $null
}

Write-Host "Qt Resource Compiler" -ForegroundColor Cyan

# Auto-detect RCC path if not provided
if ([string]::IsNullOrEmpty($RccPath)) {
    $RccPath = Find-QtRccPath
    if ([string]::IsNullOrEmpty($RccPath)) {
        Write-Host "Could not find pyside6-rcc.exe automatically!" -ForegroundColor Red
        Write-Host "Please specify the path using -RccPath parameter" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "Using specified RCC path: $RccPath" -ForegroundColor Green
}

Write-Host "Resource file: $ResourceFile" -ForegroundColor Gray
Write-Host "Output file: $OutputFile" -ForegroundColor Gray
Write-Host ""

if (!(Test-Path $ResourceFile)) {
    Write-Host "Resource file not found!" -ForegroundColor Red
    exit 1
}

if (!(Test-Path $RccPath)) {
    Write-Host "RCC executable not found!" -ForegroundColor Red
    exit 1
}

$outputDir = Split-Path $OutputFile -Parent
if (!(Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

Write-Host "Compiling resources..." -NoNewline

& $RccPath $ResourceFile -o $OutputFile

if ($LASTEXITCODE -eq 0) {
    Write-Host " Success!" -ForegroundColor Green
    exit 0
} else {
    Write-Host " Failed!" -ForegroundColor Red
    exit 1
}
