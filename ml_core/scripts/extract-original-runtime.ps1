param(
    [string]$Image = "nia-13-nonnative-speech:sjr_mdd_231011_v2",
    [string]$OutputDir = "docs\original-image-dump"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$targetDir = Join-Path $repoRoot $OutputDir

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

function Write-DumpFile {
    param(
        [string]$Name,
        [string]$Command
    )

    $outFile = Join-Path $targetDir $Name
    Write-Host "Writing $Name"
    docker run --rm $Image bash -lc $Command | Out-File -FilePath $outFile -Encoding utf8
}

Write-DumpFile -Name "python-version.txt" -Command "python --version"
Write-DumpFile -Name "which.txt" -Command "which python && which pip && which conda && which sox"
Write-DumpFile -Name "env.txt" -Command "env | sort"
Write-DumpFile -Name "pip-freeze.txt" -Command "pip freeze"
Write-DumpFile -Name "conda-list.txt" -Command "conda list"
Write-DumpFile -Name "torch.txt" -Command "python - <<'PY'
import torch
print('torch=', torch.__version__)
print('cuda_available=', torch.cuda.is_available())
print('cuda_version=', torch.version.cuda)
PY"
Write-DumpFile -Name "fairseq.txt" -Command "python - <<'PY'
import fairseq, sys
print('fairseq=', fairseq.__file__)
print('python=', sys.executable)
PY"
Write-DumpFile -Name "fairseq-git.txt" -Command "cd /opt/fairseq && git rev-parse HEAD && git status --short"
Write-DumpFile -Name "flashlight-layout.txt" -Command "ls -la /opt/conda/envs/main/lib/python3.9/site-packages/flashlight* && find /opt/conda/envs/main/lib/python3.9/site-packages/flashlight-1.0.0-py3.9-linux-x86_64.egg -maxdepth 2 -type f | sort"
Write-DumpFile -Name "flashlight-ldd.txt" -Command "ldd /opt/conda/envs/main/lib/python3.9/site-packages/flashlight-1.0.0-py3.9-linux-x86_64.egg/flashlight/lib/text/flashlight_lib_text_decoder*.so"
Write-DumpFile -Name "fairseq-tree.txt" -Command "find /opt/fairseq -maxdepth 2 | sort"
Write-DumpFile -Name "site-packages-top.txt" -Command "python - <<'PY'
import site
for path in site.getsitepackages():
    print(path)
PY
ls -la /opt/conda/envs/main/lib/python3.9/site-packages | head -n 200"

Write-Host "Runtime dump written to $targetDir"
