<#
  Builds FeedLab for Windows:
    build\FeedLab\            portable folder (embedded Python + packages + app)
    dist\FeedLab-<ver>-portable.zip
    dist\FeedLab-Setup-<ver>.exe   (if Inno Setup is installed)

  Requirements: Windows 10/11 x64, a regular Python 3.x x64 on PATH (same minor version as -PyVersion),
  internet access. Usage (PowerShell):  .\windows\build.ps1 [-Version 0.3.0] [-PyVersion 3.13.9]
#>
param(
  [string]$Version = "",
  [string]$PyVersion = ""
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$root  = Split-Path $PSScriptRoot -Parent
$build = Join-Path $root "build\FeedLab"
$dist  = Join-Path $root "dist"

if (-not $Version) {
  $Version = (Select-String -Path "$root\pyproject.toml" -Pattern '^version = "(.+)"').Matches[0].Groups[1].Value
}
if (-not $PyVersion) { $PyVersion = (python -c "import platform; print(platform.python_version())").Trim() }
$tag = ($PyVersion.Split(".")[0..1] -join "")
Write-Host "FeedLab $Version  -  Python $PyVersion (embedded)"

if (Test-Path $build) { Remove-Item -Recurse -Force $build }
New-Item -ItemType Directory -Force $build, $dist | Out-Null

# 1. embedded Python
$zip = Join-Path $env:TEMP "python-$PyVersion-embed-amd64.zip"
if (-not (Test-Path $zip)) {
  Invoke-WebRequest "https://www.python.org/ftp/python/$PyVersion/python-$PyVersion-embed-amd64.zip" -OutFile $zip
}
Expand-Archive $zip -DestinationPath "$build\python"
# search path: stdlib zip, site-packages (with .pth processing) and the app folder
Set-Content -Encoding ascii "$build\python\python$tag._pth" "python$tag.zip`r`n.`r`nLib\site-packages`r`n..\app`r`nimport site`r`n"

# 2. packages (installed by a regular Python of the same version into the embedded site-packages)
python -m pip install --upgrade pip
python -m pip install --target "$build\python\Lib\site-packages" --no-warn-script-location `
  -r "$root\requirements-desktop.txt" pip setuptools
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

# 3. the app
New-Item -ItemType Directory -Force "$build\app" | Out-Null
Copy-Item -Recurse "$root\feedlab" "$build\app\feedlab"
Copy-Item -Recurse "$root\.streamlit" "$build\app\.streamlit"
Copy-Item -Recurse "$root\docs" "$build\app\docs"
Copy-Item "$root\feedlab_main.py", "$root\README.md" "$build\app\"
Copy-Item "$root\windows\feedlab.ico" "$build\"
Get-ChildItem -Recurse -Directory -Filter "__pycache__" "$build\app" | Remove-Item -Recurse -Force

# 4. FeedLab.exe = pythonw.exe with FeedLab's icon (taskbar, window and shortcuts show FeedLab)
Copy-Item "$build\python\pythonw.exe" "$build\python\FeedLab.exe"
$rcedit = Join-Path $env:TEMP "rcedit-x64.exe"
if (-not (Test-Path $rcedit)) {
  Invoke-WebRequest "https://github.com/electron/rcedit/releases/download/v2.0.0/rcedit-x64.exe" -OutFile $rcedit
}
& $rcedit "$build\python\FeedLab.exe" --set-icon "$root\windows\feedlab.ico" `
  --set-version-string "FileDescription" "FeedLab" --set-version-string "ProductName" "FeedLab" `
  --set-version-string "CompanyName" "IZ0JNY" --set-file-version "$Version" --set-product-version "$Version"
if ($LASTEXITCODE -ne 0) { throw "rcedit failed" }

Set-Content -Encoding ascii "$build\FeedLab.bat" "@start `"`" `"%~dp0python\FeedLab.exe`" -m feedlab.desktop %*`r`n"
Set-Content -Encoding ascii "$build\FeedLab (browser).bat" "@start `"`" `"%~dp0python\FeedLab.exe`" -m feedlab.desktop --browser`r`n"
Set-Content -Encoding utf8 "$build\LEGGIMI.txt" @"
FeedLab $Version - Laboratorio di Progettazione di feed/illuminatori a microonde
Avvio: doppio clic su FeedLab.bat (finestra propria) oppure "FeedLab (browser).bat".
openEMS (opzionale, per la deep analysis full-wave): scheda "Full-wave openEMS" > Installazione.
Progetto: https://github.com/IZ0JNY/mwFeedDesign
"@

# 5. precompile and self-test with the embedded interpreter
& "$build\python\python.exe" -m compileall -q "$build\app\feedlab" | Out-Null
& "$build\python\python.exe" -m feedlab.desktop --selftest
if ($LASTEXITCODE -ne 0) { throw "self-test failed" }

# 6. portable zip
$portable = Join-Path $dist "FeedLab-$Version-portable.zip"
if (Test-Path $portable) { Remove-Item $portable }
Compress-Archive -Path $build -DestinationPath $portable -CompressionLevel Optimal

# 7. installer
$iscc = (Get-Command iscc -ErrorAction SilentlyContinue).Source
if (-not $iscc) {
  foreach ($p in @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
                   "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe")) { if (Test-Path $p) { $iscc = $p } }
}
if ($iscc) {
  & $iscc "/DMyAppVersion=$Version" "$root\windows\feedlab.iss"
  if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed" }
} else {
  Write-Warning "Inno Setup non trovato: creato solo lo zip portatile."
}
Get-ChildItem $dist | Format-Table Name, Length
