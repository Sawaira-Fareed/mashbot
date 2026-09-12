$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path -LiteralPath ".env")) {
    throw "Missing .env file in $PSScriptRoot"
}

Get-Content -LiteralPath ".env" | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line -match "^([^=]+)=(.*)$") {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
    }
}

if (-not $env:SONAR_TOKEN) {
    throw "SONAR_TOKEN is missing from .env"
}

$scanner = "D:\Semester 5\SQE\sonar-scanner\bin\sonar-scanner.bat"
if (-not (Test-Path -LiteralPath $scanner)) {
    throw "SonarScanner was not found at $scanner"
}

& $scanner "-Dsonar.host.url=$env:SONAR_HOST_URL" "-Dsonar.token=$env:SONAR_TOKEN"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
