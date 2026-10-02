$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$PythonExe = "F:\Python310\python.exe"
$InputPath = ""
$InputWasProvided = $false
$StagingPath = "data\imports\archival_news\staging\latest_archival_sources.json"
$ReportPath = "data\imports\archival_news\reports\latest_archival_import_report.json"
$UseMongo = $true
$SkipMongoIndexes = $false
$PromptMongo = $false
$NoPause = $false
$OpenRegistry = $true
$MongoHost = $env:MONGODB_ATLAS_HOST
$MongoUser = $env:MONGODB_USERNAME
$MongoDatabase = if ($env:MONGODB_DATABASE) { $env:MONGODB_DATABASE } else { "AI1SAD" }

function Show-Usage {
    Write-Host "AI1SAD archival news import launcher"
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  run_archival_news_import.bat [input-file] [options]"
    Write-Host "  run_archival_news_import.bat --input data\imports\archival_news\raw\my_sources.json --mongo"
    Write-Host "  run_archival_news_import.exe --prompt-mongo"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  --input <path>              JSON or CSV metadata file. Opens a file picker if omitted."
    Write-Host "  --staging <path>            Staging JSON output path."
    Write-Host "  --report <path>             Import report JSON output path."
    Write-Host "  --mongo                     Persist accepted records to MongoDB. Default."
    Write-Host "  --local-only, --no-mongo     Write local staging/report JSON only."
    Write-Host "  --prompt-mongo              Prompt for Mongo host, username, and password."
    Write-Host "  --mongo-host <host>         Atlas host, for example cluster0.example.mongodb.net."
    Write-Host "  --mongo-user <username>     MongoDB database username."
    Write-Host "  --mongo-database <name>     MongoDB database name. Default: AI1SAD."
    Write-Host "  --skip-mongo-indexes        Do not create MongoDB indexes before import."
    Write-Host "  --no-viewer                 Do not open the local incident registry after a successful import."
    Write-Host "  --no-pause                  Do not wait for a keypress before closing."
    Write-Host "  --help                      Show this help."
}

for ($Index = 0; $Index -lt $args.Count; $Index++) {
    $Current = $args[$Index]
    switch -Regex ($Current) {
        "^(--help|-h)$" {
            Show-Usage
            exit 0
        }
        "^--input$" {
            $Index++
            if ($Index -ge $args.Count) { throw "Missing value after --input." }
            $InputPath = $args[$Index]
            $InputWasProvided = $true
        }
        "^--staging$" {
            $Index++
            if ($Index -ge $args.Count) { throw "Missing value after --staging." }
            $StagingPath = $args[$Index]
        }
        "^--report$" {
            $Index++
            if ($Index -ge $args.Count) { throw "Missing value after --report." }
            $ReportPath = $args[$Index]
        }
        "^--mongo$" {
            $UseMongo = $true
        }
        "^(--local-only|--no-mongo)$" {
            $UseMongo = $false
        }
        "^--prompt-mongo$" {
            $PromptMongo = $true
        }
        "^--mongo-host$" {
            $Index++
            if ($Index -ge $args.Count) { throw "Missing value after --mongo-host." }
            $MongoHost = $args[$Index]
        }
        "^--mongo-user$" {
            $Index++
            if ($Index -ge $args.Count) { throw "Missing value after --mongo-user." }
            $MongoUser = $args[$Index]
        }
        "^--mongo-database$" {
            $Index++
            if ($Index -ge $args.Count) { throw "Missing value after --mongo-database." }
            $MongoDatabase = $args[$Index]
        }
        "^--skip-mongo-indexes$" {
            $SkipMongoIndexes = $true
        }
        "^--no-pause$" {
            $NoPause = $true
        }
        "^--no-viewer$" {
            $OpenRegistry = $false
        }
        default {
            if ($Current.StartsWith("-")) {
                throw "Unknown option: $Current"
            }
            $InputPath = $Current
            $InputWasProvided = $true
        }
    }
}

function ConvertFrom-SecureStringToPlainText {
    param([securestring]$SecureValue)

    $Pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
    try {
        [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Pointer)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Pointer)
    }
}

function Set-MongoUriFromPrompt {
    if (-not $script:MongoHost) {
        $script:MongoHost = Read-Host "MongoDB Atlas host, for example cluster0.example.mongodb.net"
    }
    if (-not $script:MongoUser) {
        $script:MongoUser = Read-Host "MongoDB username"
    }
    if (-not $script:MongoDatabase) {
        $script:MongoDatabase = Read-Host "MongoDB database name"
    }

    $SecureCredential = Read-Host "MongoDB password" -AsSecureString
    $PlainCredential = ConvertFrom-SecureStringToPlainText $SecureCredential
    try {
        $EncodedUser = [Uri]::EscapeDataString($script:MongoUser)
        $EncodedCredential = [Uri]::EscapeDataString($PlainCredential)
        $script:MongoHost = $script:MongoHost.Trim()
        $MongoScheme = "mongodb+srv"
        $env:MONGODB_URI = "${MongoScheme}://${EncodedUser}:${EncodedCredential}@${script:MongoHost}/?retryWrites=true&w=majority"
        $env:MONGODB_DATABASE = $script:MongoDatabase
    }
    finally {
        $PlainCredential = $null
    }
}

function Test-EnvFileHasMongoUri {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return $false
    }

    foreach ($Line in Get-Content -LiteralPath $Path) {
        if ($Line -match "^\s*MONGODB_URI\s*=\s*(.+?)\s*$") {
            $Value = $Matches[1].Trim().Trim('"').Trim("'")
            return -not [String]::IsNullOrWhiteSpace($Value)
        }
    }

    return $false
}

function Select-InputFile {
    try {
        Add-Type -AssemblyName System.Windows.Forms
        $Dialog = New-Object System.Windows.Forms.OpenFileDialog
        $Dialog.Title = "Select archival metadata JSON or CSV"
        $Dialog.Filter = "Archival metadata (*.json;*.csv)|*.json;*.csv|JSON (*.json)|*.json|CSV (*.csv)|*.csv|All files (*.*)|*.*"
        $RawFolder = Join-Path $Root "data\imports\archival_news\raw"
        if (Test-Path -LiteralPath $RawFolder) {
            $Dialog.InitialDirectory = (Resolve-Path -LiteralPath $RawFolder).Path
        }
        if ($Dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            return $Dialog.FileName
        }
    }
    catch {
        return $null
    }

    return $null
}

function Resolve-InputPath {
    if ($script:InputWasProvided) {
        if (Test-Path -LiteralPath $script:InputPath) {
            return
        }
        throw "Input metadata file not found: $script:InputPath"
    }

    $SelectedPath = Select-InputFile
    if ($SelectedPath) {
        $script:InputPath = $SelectedPath
        return
    }

    $script:InputPath = Read-Host "Path to archival JSON/CSV metadata file"
    if ([String]::IsNullOrWhiteSpace($script:InputPath)) {
        throw "Input metadata file is required."
    }
    if (-not (Test-Path -LiteralPath $script:InputPath)) {
        throw "Input metadata file not found: $script:InputPath"
    }
}

$ExitCode = 0
try {
    if (-not (Test-Path -LiteralPath $PythonExe)) {
        $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if (-not $PythonCommand) {
            throw "Could not find F:\Python310\python.exe or python on PATH."
        }
        $PythonExe = $PythonCommand.Source
    }

    Resolve-InputPath

    if ($UseMongo) {
        $EnvFile = Join-Path $Root ".env"
        if ($PromptMongo -or ((-not $env:MONGODB_URI) -and (-not (Test-EnvFileHasMongoUri $EnvFile)))) {
            Set-MongoUriFromPrompt
        }
    }

    Write-Host "AI1SAD archival news import"
    Write-Host "Input:   $InputPath"
    Write-Host "Staging: $StagingPath"
    Write-Host "Report:  $ReportPath"
    Write-Host "Mongo:   $(if ($UseMongo) { 'enabled' } else { 'disabled' })"

    $PythonArgs = @(
        "-m",
        "app.services.archival_news_tracker",
        "--input",
        $InputPath,
        "--staging",
        $StagingPath,
        "--report",
        $ReportPath
    )

    if ($UseMongo) {
        $PythonArgs += "--mongo"
        if ($SkipMongoIndexes) {
            $PythonArgs += "--skip-mongo-indexes"
        }
    }

    & $PythonExe @PythonArgs
    $ExitCode = $LASTEXITCODE

    Write-Host ""
    if ($ExitCode -eq 0) {
        Write-Host "Import completed successfully."
        if ($OpenRegistry) {
            Write-Host "Opening the AI1SAD incident registry..."
            & $PythonExe -m app.services.incident_registry_viewer
            if ($LASTEXITCODE -ne 0) {
                Write-Host "The import succeeded, but the registry viewer could not be opened." -ForegroundColor Yellow
            }
        }
    }
    else {
        Write-Host "Import finished with errors. Check the report JSON for row-level details."
    }
    Write-Host "Report: $ReportPath"
}
catch {
    $ExitCode = 2
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "Use --help for examples."
}
finally {
    if (-not $NoPause) {
        Write-Host ""
        Read-Host "Press Enter to close"
    }
}

exit $ExitCode
