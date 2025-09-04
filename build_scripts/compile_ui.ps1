# PowerShell script to compile Qt UI files
param(
    [string]$DesignerPath = "designer",
    [string]$OutputPath = "metaeditor_safetensors/views",
    [string]$UicPath = ""
)

function Find-QtUicPath {
    # Try to find via Python in PATH
    try {
        $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
        if ($pythonPath) {
            $scriptsDir = Join-Path (Split-Path (Split-Path $pythonPath -Parent) -Parent) "Scripts"
            $uicPath = Join-Path $scriptsDir "pyside6-uic.exe"
            if (Test-Path $uicPath) {
                Write-Host "Found UIC via Python installation: $uicPath" -ForegroundColor Green
                return $uicPath
            }
        }
    } catch {
        Write-Host "Python not found in PATH" -ForegroundColor Yellow
    }
    
    # Try to find pyside6-uic directly in PATH
    try {
        $uicPath = (Get-Command pyside6-uic -ErrorAction SilentlyContinue).Source
        if ($uicPath) {
            Write-Host "Found UIC in PATH: $uicPath" -ForegroundColor Green
            return $uicPath
        }
    } catch {
        # Not in PATH
    }
    
    return $null
}

Write-Host "Qt UI Compiler" -ForegroundColor Cyan

# Auto-detect UIC path if not provided
if ([string]::IsNullOrEmpty($UicPath)) {
    $UicPath = Find-QtUicPath
    if ([string]::IsNullOrEmpty($UicPath)) {
        Write-Host "Could not find pyside6-uic.exe automatically!" -ForegroundColor Red
        Write-Host "Please specify the path using -UicPath parameter" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "Using specified UIC path: $UicPath" -ForegroundColor Green
}

Write-Host "Designer folder: $DesignerPath" -ForegroundColor Gray  
Write-Host "Output folder: $OutputPath" -ForegroundColor Gray
Write-Host ""

if (!(Test-Path $DesignerPath)) {
    Write-Host "Designer folder not found!" -ForegroundColor Red
    exit 1
}

if (!(Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
}

if (!(Test-Path $UicPath)) {
    Write-Host "UIC executable not found!" -ForegroundColor Red
    exit 1
}

$uiFiles = Get-ChildItem -Path $DesignerPath -Filter "*.ui"
$successCount = 0
$failCount = 0

if ($uiFiles.Count -eq 0) {
    Write-Host "No UI files found" -ForegroundColor Yellow
    exit 0
}

Write-Host "Found $($uiFiles.Count) UI files:"

foreach ($uiFile in $uiFiles) {
    $inputFile = $uiFile.FullName
    $outputFile = Join-Path $OutputPath ($uiFile.BaseName + "_ui.py")
    
    Write-Host "  $($uiFile.Name) -> $($uiFile.BaseName)_ui.py" -NoNewline
    
    & $UicPath --from-imports $inputFile -o $outputFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " Success!" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host " Failed!" -ForegroundColor Red
        $failCount++
    }
}

Write-Host ""
Write-Host "Compilation complete: $successCount success, $failCount failed" -ForegroundColor Cyan

if ($failCount -gt 0) {
    exit 1
} else {
    exit 0
}
