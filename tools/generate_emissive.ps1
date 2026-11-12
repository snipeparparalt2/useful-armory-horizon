# Generate emissive accent masks without modifying the supplied base artwork.
# Windows PowerShell / PowerShell on Windows; System.Drawing is supplied by Windows.
Add-Type -AssemblyName System.Drawing
$textureRoot=Join-Path $PSScriptRoot '../content/assets/useful_armory/textures'
$targets=@(
 @('entity/equipment/humanoid/aquite.png','aqua'),
 @('entity/equipment/humanoid_leggings/aquite.png','aqua'),
 @('entity/equipment/humanoid/shadow_.png','shadow'),
 @('entity/equipment/humanoid_leggings/shadow_.png','shadow'),
 @('block/aquite_ore.png','aqua'),
 @('block/shadow_ore.png','shadow')
)
foreach($target in $targets){
 $file=Join-Path $textureRoot $target[0]
 $source=[System.Drawing.Bitmap]::new($file)
 $mask=[System.Drawing.Bitmap]::new($source.Width,$source.Height,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
 $selected=0
 for($y=0;$y -lt $source.Height;$y++){for($x=0;$x -lt $source.Width;$x++){
  $c=$source.GetPixel($x,$y)
  $accent=if($target[1] -eq 'aqua'){$c.G -ge 110 -and $c.G -gt $c.R*1.2 -and $c.B -gt $c.R*1.1}else{$c.B -ge 100 -and $c.B -gt $c.R*1.15 -and $c.B -gt $c.G*1.3}
  if($c.A -gt 0 -and $accent){$mask.SetPixel($x,$y,[System.Drawing.Color]::FromArgb($c.A,[int][Math]::Min(255,$c.R*1.2),[int][Math]::Min(255,$c.G*1.2),[int][Math]::Min(255,$c.B*1.2)));$selected++}
 }}
 if($selected -eq 0){throw "No emissive accents selected in $file"}
 $output=$file.Substring(0,$file.Length-4)+'_e.png'
 $mask.Save($output,[System.Drawing.Imaging.ImageFormat]::Png)
 $mask.Dispose();$source.Dispose()
 Write-Output "$($target[0]): $selected accent pixels"
}
