param(
  [string]$FlutterRoot = "C:\flutter",
  [string]$IsccPath = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
  [string]$BashPath = "C:\Program Files\Git\bin\bash.exe",
  [string]$BundleDir = "",
  [string]$Configuration = "release",
  [switch]$SkipBuild,
  [switch]$SkipPubGet,
  [switch]$SkipBundle,
  [switch]$SkipInstaller,
  [switch]$Sign,
  [string]$SigntoolPath = "",
  [string]$PfxPath = "",
  [string]$PfxPassword = "",
  [string]$CertThumbprint = "",
  [string]$TimestampUrl = "http://timestamp.digicert.com",
  [string]$VcRedistPath = ""
)

$ErrorActionPreference = "Continue"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $BundleDir) {
  $ConfigDir = switch ($Configuration.ToLower()) {
    'debug' { 'Debug' }
    'profile' { 'Profile' }
    'release' { 'Release' }
    default { throw "Unsupported Configuration '$Configuration'." }
  }
  $BundleDir = Join-Path $ProjectRoot "build\windows\x64\runner\$ConfigDir"
}

function Invoke-Native {
  param([string]$File, [string[]]$Arguments)
  & $File @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "${File} exited with code $LASTEXITCODE"
  }
}

function Find-SignTool {
  $KitsRoot = "C:\Program Files (x86)\Windows Kits\10\bin"
  if (Test-Path $KitsRoot) {
    $Candidate = Get-ChildItem $KitsRoot -Directory |
      Sort-Object Name -Descending |
      ForEach-Object { Join-Path $_.FullName "x64\signtool.exe" } |
      Where-Object { Test-Path $_ } |
      Select-Object -First 1
    if ($Candidate) { return $Candidate }
  }
  $FromPath = Get-Command signtool.exe -ErrorAction SilentlyContinue
  if ($FromPath) { return $FromPath.Source }
  return ""
}

function Find-VcRuntimeDir {
  $VsWhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
  if (Test-Path $VsWhere) {
    $InstallPath = (& $VsWhere -latest -products * `
      -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
      -property installationPath | Select-Object -First 1)
    if ($InstallPath) {
      $RedistRoot = Join-Path $InstallPath.Trim() "VC\Redist\MSVC"
      if (Test-Path $RedistRoot) {
        $Candidate = Get-ChildItem $RedistRoot -Directory |
          Sort-Object Name -Descending |
          ForEach-Object {
            Get-ChildItem (Join-Path $_.FullName "x64") -Directory `
              -Filter "Microsoft.VC*.CRT" -ErrorAction SilentlyContinue
          } |
          Where-Object { Test-Path (Join-Path $_.FullName "vcruntime140.dll") } |
          Select-Object -First 1
        if ($Candidate) { return $Candidate.FullName }
      }
    }
  }

  $Candidate = Get-ChildItem "C:\Program Files\Microsoft Visual Studio" `
    -Recurse -Directory -Filter "Microsoft.VC*.CRT" -ErrorAction SilentlyContinue |
    Where-Object {
      $_.FullName -match '\\x64\\' -and
      (Test-Path (Join-Path $_.FullName "vcruntime140.dll"))
    } |
    Sort-Object FullName -Descending |
    Select-Object -First 1
  if ($Candidate) { return $Candidate.FullName }
  return ""
}

function Resolve-VcRedist {
  param([string]$ConfiguredPath)
  $Path = $ConfiguredPath
  if (-not $Path) {
    $CacheDir = Join-Path $ProjectRoot "build_support\cache"
    New-Item -ItemType Directory -Force -Path $CacheDir | Out-Null
    $Path = Join-Path $CacheDir "vc_redist.x64.exe"
    if (-not (Test-Path $Path)) {
      Write-Host "==> downloading Microsoft Visual C++ x64 redistributable"
      Invoke-WebRequest -UseBasicParsing `
        -Uri "https://aka.ms/vs/17/release/vc_redist.x64.exe" `
        -OutFile $Path -TimeoutSec 300
    }
  }
  if (-not (Test-Path $Path)) {
    throw "Visual C++ redistributable not found at $Path."
  }
  $Signature = Get-AuthenticodeSignature $Path
  if ($Signature.Status -ne "Valid" -or
      $Signature.SignerCertificate.Subject -notmatch "O=Microsoft Corporation") {
    throw "Visual C++ redistributable signature validation failed for $Path."
  }
  return (Resolve-Path $Path).Path
}

function Test-BundledChirpDrivers {
  param([string]$Bundle)

  $Python = Join-Path $Bundle "python\python.exe"
  if (-not (Test-Path $Python)) {
    throw "Bundled Python runtime not found at '$Python'."
  }
  $Bridge = Join-Path $ProjectRoot "scripts\chirp_bridge.py"
  $Vendor = Get-ChildItem (Join-Path $ProjectRoot "assets\python") `
    -Filter "pyserial-*.whl" | Select-Object -First 1
  if (-not $Vendor) {
    throw "Bundled pyserial wheel not found under assets\python."
  }

  Write-Host "==> verifying bundled CHIRP drivers"
  & $Python $Bridge --source $Bundle --vendor $Vendor.FullName --newchirp-driver-dir (Join-Path $Bundle "newchirp_drivers") list-models | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "Bundled CHIRP driver verification failed. Ensure the selected CHIRP snapshot supports every driver in drivers\."
  }

  Write-Host "==> verifying NewChirp driver precedence"
  $Gate = Join-Path $ProjectRoot "scripts\check_bundle_drivers.py"
  & $Python -I -B $Gate --resources $Bundle --bridge $Bridge --vendor $Vendor.FullName --expect-drivers (Join-Path $ProjectRoot "drivers")
  if ($LASTEXITCODE -ne 0) {
    throw "NewChirp driver precedence check failed: a NewChirp driver is mixed into chirp\drivers or an upstream driver wins its ID."
  }
}

$FlutterBat = Join-Path $FlutterRoot "bin\flutter.bat"
if (-not (Test-Path $FlutterBat)) {
  throw "Flutter SDK not found at '$FlutterBat'. Set -FlutterRoot."
}

if (-not $SkipPubGet) {
  Write-Host "==> flutter pub get"
  Invoke-Native $FlutterBat @("pub", "get")
}

if (-not $SkipBuild) {
  Write-Host "==> flutter build windows --$Configuration"
  Invoke-Native $FlutterBat @("build", "windows", "--$Configuration")
}

if (-not (Test-Path (Join-Path $BundleDir "newchirp.exe"))) {
  throw "Flutter release bundle not found at '$BundleDir'."
}

if (-not $SkipBundle) {
  if (-not (Test-Path $BashPath)) {
    throw "Git Bash not found at '$BashPath'. Set -BashPath."
  }
  $BashDir = Split-Path $BashPath
  $Cygpath = Join-Path $BashDir "cygpath.exe"
  if (-not (Test-Path $Cygpath)) {
    $Cygpath = Join-Path (Join-Path (Split-Path $BashDir) "usr\bin") "cygpath.exe"
  }
  if (-not (Test-Path $Cygpath)) {
    throw "cygpath.exe not found. Install Git for Windows with its usr\bin directory (looked at '$(Join-Path $BashDir \"cygpath.exe\")' and '$(Join-Path (Join-Path (Split-Path $BashDir) \"usr\bin\") \"cygpath.exe\")')."
  }
  $ScriptPosix = (& $Cygpath -u (Join-Path $ProjectRoot "scripts\bundle_windows_runtime.sh")).Trim()
  $BundlePosix = (& $Cygpath -u $BundleDir).Trim()
  Write-Host "==> bundling Python + CHIRP into $BundleDir"
  Invoke-Native $BashPath @($ScriptPosix, "--bundle-dir", $BundlePosix)
}

Test-BundledChirpDrivers $BundleDir

if ($Configuration.ToLower() -ne "debug") {
  $VcRuntimeDir = Find-VcRuntimeDir
  if (-not $VcRuntimeDir) {
    throw "Visual C++ runtime files were not found. Install the Visual Studio C++ build tools or pass a machine with the VC redistributable files."
  }
  Write-Host "==> bundling Visual C++ runtime from $VcRuntimeDir"
  Copy-Item (Join-Path $VcRuntimeDir "*.dll") $BundleDir -Force
}

$VcRedist = ""
if ($Configuration.ToLower() -ne "debug") {
  $VcRedist = Resolve-VcRedist $VcRedistPath
  Write-Host "==> bundling Microsoft VC++ redistributable from $VcRedist"
}

$Pubspec = Join-Path $ProjectRoot "pubspec.yaml"
$VersionLine = (Select-String -Path $Pubspec -Pattern '^version:\s*(\S+)' |
  Select-Object -First 1)
if (-not $VersionLine) {
  throw "Could not read the version from pubspec.yaml."
}
$Version = $VersionLine.Matches[0].Groups[1].Value
$DisplayVersion = $Version.Split('+')[0]

if (-not $SkipInstaller) {
  if (-not (Test-Path $IsccPath)) {
    throw "Inno Setup ISCC not found at '$IsccPath'. Set -IsccPath."
  }
  $Iss = Join-Path $ProjectRoot "installer\newchirp.iss"
  Write-Host "==> compiling installer for version $DisplayVersion"
  $IsccArgs = @(
    "/DSourceDir=$BundleDir",
    "/DMyAppVersion=$DisplayVersion",
    "/DMyAppPublisher=com.rickext.newchirp"
  )
  if ($VcRedist) {
    $IsccArgs += "/DVcRedistPath=$VcRedist"
  }
  $IsccArgs += $Iss
  Invoke-Native $IsccPath $IsccArgs
}

$Installer = Join-Path $ProjectRoot "build\NewChirp-Installer-$DisplayVersion.exe"

if ($Sign) {
  if (-not $CertThumbprint -and -not (Test-Path $PfxPath)) {
    throw "Signing requested (-Sign) but no certificate is configured. Pass -PfxPath/-PfxPassword (pfx) or -CertThumbprint (store cert), or omit -Sign to build unsigned."
  }
  if (-not $SigntoolPath) { $SigntoolPath = Find-SignTool }
  if (-not $SigntoolPath -or -not (Test-Path $SigntoolPath)) {
    throw "signtool.exe not found. Install the Windows SDK (Windows Kits) or pass -SigntoolPath."
  }

  $SignArgs = @("sign", "/fd", "SHA256", "/tr", $TimestampUrl, "/td", "SHA256")
  if ($CertThumbprint) {
    $SignArgs += @("/sha1", $CertThumbprint)
    Write-Host "==> signing installer with certificate thumbprint $CertThumbprint"
  } else {
    $SignArgs += @("/f", (Resolve-Path $PfxPath).Path, "/p", $PfxPassword)
    Write-Host "==> signing installer with PFX '$PfxPath'"
  }
  $SignArgs += $Installer

  Invoke-Native $SigntoolPath $SignArgs
  Write-Host "==> signed: $Installer"
}

Write-Host "Done. Installer: $Installer"
