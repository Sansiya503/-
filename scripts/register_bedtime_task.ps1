param(
    [string]$TaskName = "TelegramBedtimeReminder",
    [string]$At = "23:55"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RunScript = Join-Path $ScriptDir "run_bedtime_reminder.ps1"

if (-not (Test-Path $RunScript)) {
    throw "Cannot find run script: $RunScript"
}

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$RunScript`""

$Trigger = New-ScheduledTaskTrigger -Daily -At $At
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Description "Send a daily Telegram bedtime reminder." `
    -Force

Write-Host "Registered task '$TaskName' to run daily at $At."
