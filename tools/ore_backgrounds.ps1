param([Parameter(Mandatory=$true)][string]$CobblestoneTexture)
Add-Type -AssemblyName System.Drawing
$root=Join-Path $PSScriptRoot '../content/assets/useful_armory/textures/block'
$code=Get-Content (Join-Path $PSScriptRoot 'gen_textures.py') -Raw
$cobble=[System.Drawing.Bitmap]::new((Resolve-Path $CobblestoneTexture).Path)
if($cobble.Width -ne 16 -or $cobble.Height -ne 16){throw 'Expected the vanilla 16x16 cobblestone texture'}
foreach($pair in @(@('aquite_ore','shards'),@('colosifite_ore','nuggets'),@('shadow_ore','voids'))){
 $section=[regex]::Match($code,"(?s)'"+$pair[1]+"': \[(.*?)\]").Groups[1].Value
 $rows=@([regex]::Matches($section,"'([.0-9]{16})'") | ForEach-Object {$_.Groups[1].Value})
 if($rows.Count -ne 16){throw 'Mineral mask not found'}
 $file=Join-Path $root ($pair[0]+'.png')
 $original=[System.Drawing.Bitmap]::new($file)
 $output=[System.Drawing.Bitmap]::new(16,16,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
 $background=0
 for($y=0;$y -lt 16;$y++){for($x=0;$x -lt 16;$x++){
  if($rows[$y][$x] -eq '.'){$color=$cobble.GetPixel($x,$y);$background++}else{$color=$original.GetPixel($x,$y)}
  $output.SetPixel($x,$y,$color)
 }}
 $original.Dispose();$output.Save($file,[System.Drawing.Imaging.ImageFormat]::Png);$output.Dispose()
 Write-Output "$($pair[0]): $background background pixels exactly match cobblestone; mineral pixels preserved"
}
$cobble.Dispose()
