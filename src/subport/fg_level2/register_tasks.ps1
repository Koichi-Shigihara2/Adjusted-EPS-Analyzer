# F&G Level2 TQQQ 自動売買 タスクスケジューラ登録スクリプト
# 管理者権限で実行してください
#
# 実行:
#   Right-click → "管理者として実行" で PowerShell を開いてから
#   cd C:\Users\shigi\Documents\On-a-journey-git
#   .\src\subport\fg_level2\register_tasks.ps1

$RepoRoot = "C:\Users\shigi\Documents\On-a-journey-git"
$PythonPath = (Get-Command python).Source

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "F&G Level2 タスクスケジューラ登録" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ============================================================
# タスク1: エントリー判定（毎日 22:30 JST）
# GitHub Actionsが22:00にsignal.jsonを更新するので
# 30分後にpull → 判定 → 発注
# ============================================================

$action1 = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "src\subport\fg_level2\trader.py --entry" `
    -WorkingDirectory $RepoRoot

$trigger1 = New-ScheduledTaskTrigger `
    -Daily -At "10:30PM"

$settings1 = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable `
    -WakeToRun $false

# 既存タスクを削除してから登録
Unregister-ScheduledTask -TaskName "FG_Level2_Entry" -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask `
    -TaskName "FG_Level2_Entry" `
    -Action $action1 `
    -Trigger $trigger1 `
    -Settings $settings1 `
    -Description "F&G Level2 TQQQ エントリー判定・発注（毎日22:30）"

Write-Host "[1] FG_Level2_Entry 登録完了 (毎日 22:30)" -ForegroundColor Green

# ============================================================
# タスク2: ポジション監視（毎日 08:00 JST）
# 米国市場開場前（ET 19:00）にポジション確認
# 利確/損切条件をチェック → 条件成立なら決済
# ============================================================

$action2 = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "src\subport\fg_level2\trader.py --monitor" `
    -WorkingDirectory $RepoRoot

$trigger2 = New-ScheduledTaskTrigger `
    -Daily -At "8:00AM"

$settings2 = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable `
    -WakeToRun $false

Unregister-ScheduledTask -TaskName "FG_Level2_Monitor" -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask `
    -TaskName "FG_Level2_Monitor" `
    -Action $action2 `
    -Trigger $trigger2 `
    -Settings $settings2 `
    -Description "F&G Level2 TQQQ ポジション監視・決済（毎日08:00）"

Write-Host "[2] FG_Level2_Monitor 登録完了 (毎日 08:00)" -ForegroundColor Green

# ============================================================
# 確認
# ============================================================

Write-Host ""
Write-Host "登録済みタスク一覧:" -ForegroundColor Cyan
Get-ScheduledTask | Where-Object { $_.TaskName -like "FG_Level2*" } | `
    Format-Table TaskName, State -AutoSize

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "完全自動化フロー:" -ForegroundColor Cyan
Write-Host "  GitHub Actions 22:00 → signal.py実行 → signal.json更新" -ForegroundColor White
Write-Host "  ローカルPC     22:30 → trader.py --entry → git pull → 発注" -ForegroundColor White
Write-Host "  ローカルPC     08:00 → trader.py --monitor → 利確/損切" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
