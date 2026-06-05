#Requires -Version 5.1
<#
.SYNOPSIS
    啟動 SakuraNavi Backend（production 環境）
.DESCRIPTION
    1. 載入 .env.production
    2. 確認資料庫可連線
    3. 確認 Alembic migration 是否為最新
    4. 若不為最新，詢問是否自動升級；失敗時詢問是否刪除重建（需 DB 超級使用者密碼）
    5. 清除殘留的舊 uvicorn 程序（防止重複啟動造成程序積累）
    6. 啟動 uvicorn（無 --reload，workers 依 CPU 核心數）

.NOTES
    正式環境注意事項：
    - 請勿在不受信任的網路上執行此腳本
    - 建議透過 systemd / Docker / PM2 管理 process，而非直接執行此腳本
    - 刪除重建資料庫將清除所有資料，生產環境請三思
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ─── 路徑 ──────────────────────────────────────────────────────────────────────
$ROOT      = Split-Path -Parent $PSScriptRoot
$ENV_FILE  = Join-Path $ROOT '.env.production'
$VENV_PY   = Join-Path $ROOT '.venv\Scripts\python.exe'
$VENV_UV   = Join-Path $ROOT '.venv\Scripts\uvicorn.exe'
$ALEMBIC   = Join-Path $ROOT '.venv\Scripts\alembic.exe'

# ─── 顏色工具 ──────────────────────────────────────────────────────────────────
function Write-Step  { param($msg) Write-Host "  $msg" -ForegroundColor Cyan }
function Write-OK    { param($msg) Write-Host "  [OK]  $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "  [!!]  $msg" -ForegroundColor Yellow }
function Write-Err   { param($msg) Write-Host "  [ERR] $msg" -ForegroundColor Red }
function Write-Title { param($msg) Write-Host "`n===  $msg  ===" -ForegroundColor Magenta }

# ─── 原生命令工具 ────────────────────────────────────────────────────────────────
function Invoke-NativeCapture {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [string[]]$Arguments = @()
    )

    $oldEap = $ErrorActionPreference
    try {
        # 某些工具（如 Alembic）會把 INFO 寫到 stderr；這裡只收集文字，不把它當例外。
        $ErrorActionPreference = 'Continue'
        $lines = & $Command @Arguments 2>&1 | ForEach-Object { $_.ToString() }
        return [PSCustomObject]@{
            ExitCode = $LASTEXITCODE
            Output   = (($lines | Where-Object { $_ -ne $null }) -join [Environment]::NewLine).Trim()
        }
    } finally {
        $ErrorActionPreference = $oldEap
    }
}

function Get-AlembicRevisionLine {
    param([string]$RawText)

    $line = ($RawText -split "`r?`n" |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ -and ($_ -notmatch '^INFO\s+\[') } |
        Select-Object -Last 1)

    if ($line) { return $line }
    return '(無 revision，可能尚未建立 alembic_version)'
}

# ─── 讀取 .env 檔案 ────────────────────────────────────────────────────────────
function Import-EnvFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        Write-Err ".env 檔案不存在：$Path"
        exit 1
    }
    $values = @{}
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#')) {
            $idx = $line.IndexOf('=')
            if ($idx -gt 0) {
                $key = $line.Substring(0, $idx).Trim()
                $val = $line.Substring($idx + 1).Trim().Trim('"').Trim("'")
                $values[$key] = $val
                [System.Environment]::SetEnvironmentVariable($key, $val, 'Process')
            }
        }
    }
    return $values
}

# ─── 解析 DATABASE_URL ─────────────────────────────────────────────────────────
function Parse-DatabaseUrl {
    param([string]$Url)
    if ($Url -match '^postgresql\+psycopg://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+)$') {
        return @{
            User   = $Matches[1]
            Pass   = $Matches[2]
            Host   = $Matches[3]
            Port   = if ($Matches[4]) { $Matches[4] } else { '5432' }
            DbName = $Matches[5]
        }
    }
    Write-Err "無法解析 DATABASE_URL 格式：$Url"
    exit 1
}

# ─── 確認 psql 可用 ────────────────────────────────────────────────────────────
function Get-PsqlPath {
    $psql = Get-Command psql -ErrorAction SilentlyContinue
    if (-not $psql) {
        Write-Err "找不到 psql 指令，請確認 PostgreSQL bin 已加入 PATH。"
        exit 1
    }
    return $psql.Source
}


# ─── 步驟 1：確認 .env 載入 ────────────────────────────────────────────────────
Write-Title "SakuraNavi Backend — production"
Write-Warn "正式環境啟動中，請確認設定正確。"
Write-Step "載入 $ENV_FILE ..."
$env_values = Import-EnvFile -Path $ENV_FILE
$env:APP_ENV = 'production'
Write-OK "環境變數已載入（APP_ENV=production）"

# ─── 步驟 2：確認資料庫連線 ────────────────────────────────────────────────────
Write-Step "確認資料庫連線 ..."
$db = Parse-DatabaseUrl -Url $env_values['DATABASE_URL']
$psql_exe = Get-PsqlPath

$env:PGPASSWORD = $db.Pass
$result = & $psql_exe -U $db.User -h $db.Host -p $db.Port -d $db.DbName `
    -c 'SELECT 1' -t -q 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Err "無法連線至資料庫 $($db.DbName)@$($db.Host):$($db.Port)"
    Write-Host "  錯誤訊息：$result" -ForegroundColor DarkRed
    Write-Warn "請確認 PostgreSQL 已啟動，且 .env.production 中的 DATABASE_URL 正確。"
    exit 1
}
Write-OK "資料庫連線成功（$($db.DbName)@$($db.Host):$($db.Port)）"

# ─── 步驟 3：確認 migration 版本 ───────────────────────────────────────────────
Write-Step "確認 Alembic migration 狀態 ..."
Push-Location $ROOT

$current = Invoke-NativeCapture -Command $ALEMBIC -Arguments @('current')
if ($current.ExitCode -ne 0) {
    Write-Err "alembic current 執行失敗。"
    if ($current.Output) { Write-Host "  錯誤訊息：$($current.Output)" -ForegroundColor DarkRed }
    Pop-Location
    exit 1
}

$heads = Invoke-NativeCapture -Command $ALEMBIC -Arguments @('heads')
if ($heads.ExitCode -ne 0) {
    Write-Err "alembic heads 執行失敗。"
    if ($heads.Output) { Write-Host "  錯誤訊息：$($heads.Output)" -ForegroundColor DarkRed }
    Pop-Location
    exit 1
}

$current_raw = $current.Output
$heads_raw   = $heads.Output

$is_latest = $current_raw -match '\(head\)'

if ($is_latest) {
    Write-OK "Migration 已是最新版本。"
} else {
    $current_line = Get-AlembicRevisionLine -RawText $current_raw
    $head_line    = Get-AlembicRevisionLine -RawText $heads_raw
    Write-Warn "Migration 尚未為最新版本。"
    Write-Host "  目前版本：$current_line" -ForegroundColor DarkYellow
    Write-Host "  最新版本：$head_line"    -ForegroundColor DarkYellow

    Write-Host ""
    Write-Warn "【正式環境警告】升級 migration 前建議先備份資料庫。"
    $ans = Read-Host "  是否執行 alembic upgrade head？[Y/n]"
    if ($ans -match '^[Yy]$' -or $ans -eq '') {
        Write-Step "執行 alembic upgrade head ..."
        $upgrade = Invoke-NativeCapture -Command $ALEMBIC -Arguments @('upgrade', 'head')
        if ($upgrade.Output) { $upgrade.Output -split [Environment]::NewLine | ForEach-Object { Write-Host "    $_" } }

        if ($upgrade.ExitCode -ne 0) {
            Write-Err "upgrade head 執行失敗。"
            Write-Host ""
            Write-Warn "【正式環境警告】刪除重建將永久清除所有資料，此操作不可逆。"
            $rebuild = Read-Host "  是否刪除並重建資料庫？（輸入 YES 確認，其他視為取消）"
            if ($rebuild -ceq 'YES') {
                # ── 要求超級使用者密碼 ────────────────────────────────────────
                $su_pass_sec = Read-Host "  請輸入 postgres 超級使用者密碼" -AsSecureString
                $BSTR        = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($su_pass_sec)
                $su_pass     = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
                [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)

                Write-Step "終止現有連線 ..."
                $env:PGPASSWORD = $su_pass
                & $psql_exe -U postgres -h $db.Host -p $db.Port -d postgres `
                    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$($db.DbName)' AND pid <> pg_backend_pid();" -q 2>&1 | Out-Null

                Write-Step "刪除資料庫 $($db.DbName) ..."
                & $psql_exe -U postgres -h $db.Host -p $db.Port -d postgres `
                    -c "DROP DATABASE IF EXISTS $($db.DbName);" -q 2>&1 | Out-Null

                Write-Step "重建資料庫 $($db.DbName) ..."
                & $psql_exe -U postgres -h $db.Host -p $db.Port -d postgres `
                    -c "CREATE DATABASE $($db.DbName) OWNER $($db.User) ENCODING 'UTF8';" 2>&1 | Out-Null

                if ($LASTEXITCODE -ne 0) {
                    Write-Err "無法建立資料庫，請手動處理。"
                    Pop-Location; exit 1
                }

                # 授予必要權限
                $env:PGPASSWORD = $su_pass
                & $psql_exe -U postgres -h $db.Host -p $db.Port -d $db.DbName `
                    -c "REVOKE ALL ON SCHEMA public FROM PUBLIC; GRANT USAGE, CREATE ON SCHEMA public TO $($db.User); ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT,INSERT,UPDATE,DELETE ON TABLES TO $($db.User); ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE,SELECT ON SEQUENCES TO $($db.User);" -q 2>&1 | Out-Null

                Write-Step "重新執行 alembic upgrade head ..."
                $env:PGPASSWORD = $db.Pass
                $upgrade_retry = Invoke-NativeCapture -Command $ALEMBIC -Arguments @('upgrade', 'head')
                if ($upgrade_retry.Output) { $upgrade_retry.Output -split [Environment]::NewLine | ForEach-Object { Write-Host "    $_" } }

                if ($upgrade_retry.ExitCode -ne 0) {
                    Write-Err "重建後 migration 仍失敗，請人工排查。"
                    Pop-Location; exit 1
                }
                Write-OK "資料庫重建完成並 migration 至最新版本。"
            } else {
                Write-Warn "已取消重建，伺服器不啟動。"
                Pop-Location; exit 1
            }
        } else {
            Write-OK "Migration 升級完成。"
        }
    } else {
        Write-Warn "已略過 migration，直接啟動（資料庫結構可能不符合預期）。"
    }
}

Pop-Location

# ─── 步驟 4：清除殘留的舊程序 ─────────────────────────────────────────────────
Write-Title "清理舊有程序"
Write-Step "檢查是否有殘留的 uvicorn / worker 程序 ..."

$staleProcs = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -match [regex]::Escape($VENV_UV) -or
    $_.CommandLine -match [regex]::Escape($ROOT.Replace('\', '\\')) -and $_.CommandLine -match 'multiprocessing-fork'
}

if ($staleProcs) {
    Write-Warn "發現 $($staleProcs.Count) 個殘留程序，正在終止 ..."
    $staleProcs | ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
    # 等候子程序完全退出
    Start-Sleep -Milliseconds 1000
    Write-OK "殘留程序已清除。"
} else {
    Write-OK "無殘留程序。"
}

# ─── 步驟 5：決定 worker 數量 ─────────────────────────────────────
$min_workers     = 4
$max_workers     = 8
$default_workers = 4

# Windows multiprocess has socket inheritance issues with >1 workers;
# force 1 worker on Windows to avoid OSError 10022 at sock.listen().
$is_windows = [Environment]::OSVersion.Platform -eq 'Win32NT'
if ($is_windows) {
    $workers = 1
    Write-Warn "Windows 環境偵測到，將使用 1 個 worker（避免 multiprocess socket 錯誤）。"
} elseif ($env_values.ContainsKey('UVICORN_WORKERS') -and $env_values['UVICORN_WORKERS']) {
    $parsed_workers = 0
    if ([int]::TryParse($env_values['UVICORN_WORKERS'], [ref]$parsed_workers)) {
        if ($parsed_workers -lt $min_workers) {
            Write-Warn "UVICORN_WORKERS=$parsed_workers 小於 $min_workers，已自動調整為 $min_workers。"
            $workers = $min_workers
        } elseif ($parsed_workers -gt $max_workers) {
            Write-Warn "UVICORN_WORKERS=$parsed_workers 大於 $max_workers，已自動調整為 $max_workers。"
            $workers = $max_workers
        } else {
            $workers = $parsed_workers
        }
    } else {
        Write-Warn "UVICORN_WORKERS='$($env_values['UVICORN_WORKERS'])' 不是有效整數，改用預設值 $default_workers。"
        $workers = $default_workers
    }
} else {
    Write-Step "未設定 UVICORN_WORKERS，使用預設 workers=$default_workers（可在 .env.production 設定 4~8）。"
    $workers = $default_workers
}

# ─── 步驟 6：啟動 uvicorn ──────────────────────────────────────────────────────
$PORT = if ($env_values.ContainsKey('PORT')) { $env_values['PORT'] } else { '8080' }
Write-Title "啟動 uvicorn（production，port $PORT，workers $workers）"
Write-Warn "Swagger UI 已停用（production 模式）。"

& $VENV_UV app.main:app `
    --host 0.0.0.0 `
    --port $PORT `
    --loop app.core.event_loop:selector_event_loop `
    --workers $workers `
    --log-level warning
