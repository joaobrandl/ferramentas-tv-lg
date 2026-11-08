# Prepara as fotos da tela de descanso do Free My TV.
# Pega as fotos de "Fotos da tela de descanso\<tema>\" (qualquer tamanho: JPG, PNG, BMP, WEBP ou HEIC) e grava copias
# leves, 1920 x 1080 em JPEG (qualidade 92), em free-my-tv\saver-photos.local\<tema>\, que o build coloca no app.
# Por que: a TV e antiga e tem pouca memoria. Uma foto de celular (12 MP) ocupa ~48 MB aberta; em 1920 x 1080, ~8 MB
# (medido na TV com 1280 x 720 o app ficou em 87 MB; 1920 x 1080 da 1,5x mais detalhe na tela 4K). Use fotos de pelo
# menos 1920 x 1080: menores ficam esticadas e perdem nitidez.
# Foto deitada: preenche a tela (corta as sobras). Foto em pe ou quadrada: inteira, com faixas pretas dos lados.
# WEBP (comum ao salvar do Pinterest) e HEIC (iPhone) passam pelo leitor de imagens do proprio Windows (WIC); se ele nao
# souber abrir algum arquivo, ou se o arquivo estiver estragado, o script avisa e pula so aquele arquivo.
# As fotos prontas so sao trocadas no fim, quando tudo deu certo. So usa o que ja vem no Windows; nao baixa nada.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName PresentationCore

$src = Join-Path $PSScriptRoot '..\Fotos da tela de descanso'
$dst = Join-Path $PSScriptRoot '..\free-my-tv\saver-photos.local'
$tmp = "$dst.novo"
if (-not (Test-Path $src)) { Write-Host 'Sem a pasta "Fotos da tela de descanso": nada a preparar.'; exit 0 }
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
New-Item -ItemType Directory -Force $tmp | Out-Null

$W = 1920; $H = 1080
$jpeg = [Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$quality = New-Object Drawing.Imaging.EncoderParameters 1
$quality.Param[0] = New-Object Drawing.Imaging.EncoderParameter ([Drawing.Imaging.Encoder]::Quality), ([long]92)

# Nome de pasta sem acento nem espaco, para o caminho dentro do app.
function Slug([string]$s) {
  $d = $s.Normalize([Text.NormalizationForm]::FormD)
  $b = New-Object Text.StringBuilder
  foreach ($c in $d.ToCharArray()) {
    if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($c) -ne 'NonSpacingMark') { [void]$b.Append($c) }
  }
  return (($b.ToString().ToLower()) -replace '[^a-z0-9]+', '-').Trim('-')
}

# Gira a foto conforme a orientacao gravada pela camera (EXIF 1 a 8).
function Girar($img, [int]$o) {
  switch ($o) {
    2 { $img.RotateFlip('RotateNoneFlipX') }
    3 { $img.RotateFlip('Rotate180FlipNone') }
    4 { $img.RotateFlip('Rotate180FlipX') }
    5 { $img.RotateFlip('Rotate90FlipX') }
    6 { $img.RotateFlip('Rotate90FlipNone') }
    7 { $img.RotateFlip('Rotate270FlipX') }
    8 { $img.RotateFlip('Rotate270FlipNone') }
  }
}

# Abre a foto como System.Drawing.Image ja na orientacao certa. JPG, PNG e BMP direto; os outros pelo WIC do Windows
# (convertidos para PNG na memoria). Devolve tambem o que precisa ser fechado depois.
function Abrir($path) {
  $ext = [IO.Path]::GetExtension($path).ToLower()
  if ($ext -in '.jpg', '.jpeg', '.png', '.bmp') {
    $img = [Drawing.Image]::FromFile($path)
    if ($img.PropertyIdList -contains 0x0112) { Girar $img ([int]$img.GetPropertyItem(0x0112).Value[0]) }
    return @($img, $null)
  }
  $file = [IO.File]::OpenRead($path)
  try {
    $dec = [System.Windows.Media.Imaging.BitmapDecoder]::Create($file, [System.Windows.Media.Imaging.BitmapCreateOptions]::None,
      [System.Windows.Media.Imaging.BitmapCacheOption]::OnLoad)
    $frame = $dec.Frames[0]
    $o = 1
    try { $q = $frame.Metadata.GetQuery('System.Photo.Orientation'); if ($q) { $o = [int]$q } } catch {}
    $png = New-Object System.Windows.Media.Imaging.PngBitmapEncoder
    $png.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($frame))
    $mem = New-Object IO.MemoryStream
    $png.Save($mem)
    $mem.Position = 0
    $img = [Drawing.Image]::FromStream($mem)
    Girar $img $o
    return @($img, $mem)
  } finally { $file.Dispose() }
}

$total = 0; $pulados = 0
Get-ChildItem -LiteralPath $src -Directory | Sort-Object Name | ForEach-Object {
  $tema = Slug $_.Name
  if (-not $tema) { return }
  $saida = Join-Path $tmp $tema
  New-Item -ItemType Directory -Force $saida | Out-Null
  $n = 0
  Get-ChildItem -LiteralPath $_.FullName -File | Where-Object { $_.Extension -match '^\.(jpe?g|png|bmp|webp|heic|heif)$' } |
    Sort-Object Name | ForEach-Object {
      $arquivo = $_
      $img = $null; $mem = $null
      try {
        $aberta = Abrir $arquivo.FullName
        $img = $aberta[0]; $mem = $aberta[1]
        $bmp = New-Object Drawing.Bitmap $W, $H
        $g = [Drawing.Graphics]::FromImage($bmp)
        $g.InterpolationMode = 'HighQualityBicubic'
        $g.PixelOffsetMode = 'HighQuality'
        $g.CompositingQuality = 'HighQuality'
        $g.Clear([Drawing.Color]::Black)
        $atts = New-Object Drawing.Imaging.ImageAttributes
        $atts.SetWrapMode('TileFlipXY')   # sem borda clara nas beiradas
        if ($img.Width / $img.Height -ge 1.2) {
          # Deitada: cobre a tela inteira, cortando o que sobra no meio.
          $s = [Math]::Max($W / $img.Width, $H / $img.Height)
          $sw = $W / $s; $sh = $H / $s
          $sx = ($img.Width - $sw) / 2; $sy = ($img.Height - $sh) / 2
          $g.DrawImage($img, (New-Object Drawing.Rectangle 0, 0, $W, $H), $sx, $sy, $sw, $sh, 'Pixel', $atts)
        } else {
          # Em pe ou quadrada: inteira, centralizada no preto.
          $s = [Math]::Min($W / $img.Width, $H / $img.Height)
          $dw = [int]($img.Width * $s); $dh = [int]($img.Height * $s)
          $g.DrawImage($img, (New-Object Drawing.Rectangle ([int](($W - $dw) / 2)), ([int](($H - $dh) / 2)), $dw, $dh),
            0, 0, $img.Width, $img.Height, 'Pixel', $atts)
        }
        $n++
        $bmp.Save((Join-Path $saida ('{0:D2}.jpg' -f $n)), $jpeg, $quality)
        $g.Dispose(); $bmp.Dispose(); $atts.Dispose()
      } catch {
        $pulados++
        Write-Host ("  pulei '{0}': nao consegui abrir como imagem" -f $arquivo.Name) -ForegroundColor Yellow
      } finally {
        if ($img) { $img.Dispose() }
        if ($mem) { $mem.Dispose() }
      }
    }
  Write-Host ("  {0}: {1} foto(s)" -f $_.Name, $n)
  $total += $n
}

# Tudo pronto: so agora as fotos novas tomam o lugar das antigas.
if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
Move-Item $tmp $dst
Write-Host "Fotos prontas: $total$(if ($pulados) { " ($pulados arquivo(s) pulado(s))" })"
