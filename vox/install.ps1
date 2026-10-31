# The Vox effects are part of the main skill now - this runs the main installer.
& powershell -ExecutionPolicy Bypass -File (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..\install.ps1") @args
