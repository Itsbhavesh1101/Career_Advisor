param(
  [string]$ProjectId = $(throw "ProjectId is required"),
  [string]$Region = "asia-south1",
  [string]$Service = "sage-career-backend",
  [string]$EnvFile = "deploy/cloud-run/backend.env.yaml"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "../..")
$BackendPath = Join-Path $RepoRoot "backend"
$EnvPath = Join-Path $RepoRoot $EnvFile

if (!(Test-Path $EnvPath)) {
  throw "Missing env file: $EnvPath. Copy deploy/cloud-run/backend.env.yaml.example to deploy/cloud-run/backend.env.yaml and fill production values."
}

$EnvContent = Get-Content $EnvPath -Raw
$JwtSecretMatch = [regex]::Match($EnvContent, '(?m)^\s*JWT_SECRET\s*:\s*[''"]?(?<value>[^''"#\r\n]+)')
if (!$JwtSecretMatch.Success) {
  throw "Missing JWT_SECRET in $EnvPath. Add a production secret with at least 32 characters before deploying."
}

$JwtSecret = $JwtSecretMatch.Groups["value"].Value.Trim()
if ($JwtSecret.Length -lt 32 -or $JwtSecret -like "__SET_*" -or $JwtSecret -like "replace-with*") {
  throw "JWT_SECRET in $EnvPath must be replaced with a real production secret of at least 32 characters."
}

$GcloudCommand = (Get-Command gcloud.cmd -ErrorAction SilentlyContinue).Source
if (!$GcloudCommand) {
  $GcloudCommand = (Get-Command gcloud -ErrorAction Stop).Source
}

& $GcloudCommand config set project $ProjectId
& $GcloudCommand run deploy $Service `
  --source $BackendPath `
  --region $Region `
  --port 8080 `
  --env-vars-file $EnvPath `
  --allow-unauthenticated
