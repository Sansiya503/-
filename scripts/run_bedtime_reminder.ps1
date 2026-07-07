$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$AgentPath = Join-Path $ProjectRoot "bedtime_reminder.py"
$BundledPython = "C:\Users\analo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

$requiredVars = @(
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "TIMEZONE"
)

$missing = @()
foreach ($name in $requiredVars) {
    $processValue = [Environment]::GetEnvironmentVariable($name, "Process")
    $userValue = [Environment]::GetEnvironmentVariable($name, "User")

    if ([string]::IsNullOrWhiteSpace($processValue) -and -not [string]::IsNullOrWhiteSpace($userValue)) {
        [Environment]::SetEnvironmentVariable($name, $userValue, "Process")
        $processValue = $userValue
    }

    if ([string]::IsNullOrWhiteSpace($processValue)) {
        $missing += $name
    }
}

if ($missing.Count -gt 0) {
    throw "Missing environment variables: $($missing -join ', ')"
}

if (Test-Path $BundledPython) {
    $Python = $BundledPython
} else {
    $Python = "python"
}

Push-Location $ProjectRoot
try {
    & $Python $AgentPath
} finally {
    Pop-Location
}
