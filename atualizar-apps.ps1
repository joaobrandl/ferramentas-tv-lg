# Atualiza a lista de apps do Free My TV e reinstala na TV.
# Use depois de instalar ou remover apps na TV. A TV precisa estar ligada e no cabo do PC.
$ErrorActionPreference = 'Stop'
$repo = Join-Path $PSScriptRoot '..\free-my-tv'
$py = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
$env:PYTHONIOENCODING = 'utf-8'

function Pare($msg) { Write-Host ''; Write-Host $msg -ForegroundColor Red; Read-Host 'Aperte Enter para fechar'; exit 1 }

if (-not (Test-Path $py)) { Pare 'Python nao encontrado.' }

# A TV pelo endereco fisico do cabo dela (achar_tv.py): o IP muda quando ela reinicia de verdade (queda de luz).
Write-Host 'Procurando a TV...'
$ip = & $py -I (Join-Path $PSScriptRoot 'achar_tv.py') | Select-Object -First 1
if (-not $ip) { Pare 'Nao achei a TV no cabo do PC. Confira se ela esta ligada, com o cabo no PC, e se o compartilhamento de internet do Windows esta ligado.' }
Write-Host "TV encontrada em $ip" -ForegroundColor Green

Set-Location $repo
Write-Host ''; Write-Host '1/4 Lendo os apps da TV (se a TV pedir permissao, aceite no controle)...'
& $py webos\apps.py $ip
if ($LASTEXITCODE -ne 0) { Pare 'Falhou ao ler os apps.' }
Write-Host ''; Write-Host '2/4 Preparando as fotos da tela de descanso...'
try { & (Join-Path $PSScriptRoot 'preparar-fotos.ps1') } catch { Pare "Falhou ao preparar as fotos: $_" }
Write-Host ''; Write-Host '3/4 Gerando o Free My TV...'
& $py webos\build.py --hd --langs pt,en
if ($LASTEXITCODE -ne 0) { Pare 'Falhou ao gerar o app.' }
Write-Host ''; Write-Host '4/4 Instalando na TV...'
& $py webos\install.py $ip
if ($LASTEXITCODE -ne 0) { Pare 'Falhou ao instalar. Confira se o Developer Mode da TV esta ativo.' }
Write-Host ''; Write-Host 'Pronto! O Free My TV foi atualizado e esta aberto na TV.' -ForegroundColor Green
Read-Host 'Aperte Enter para fechar'
