param (
    [switch] $Publish
)

if($PSCommandPath -eq $null) {
	Write-Host "Using MyInvoction.MyCommand.Path";
	$CommandRootPath = (Split-Path -Parent $MyInvocation.MyCommand.Path);
} else {
	Write-Host "Using PSCommandPath";
	$CommandRootPath = (Split-Path -Parent $PSCommandPath);
}

$CWD = Get-Location;

Import-Module "$CWD\.appveyor\modules\AppVeyor-Helper.psm1" -Verbose -Force;
Import-Module "$CWD\.appveyor\modules\Invoke-MsBuild.psm1" -Verbose -Force;

$ENV:APPVEYOR_BUILD_FOLDER = "$CWD\";


Invoke-MsBuild -Path $CWD\.build/build.msbuild

$testResults = (& python -m unittest discover -v -s tests -p *.py *>&1);
if ($LASTEXITCODE -ne 0) {
    $testResults | Write-Error;
    exit $LASTEXITCODE;
} else {
    $testResults | Write-Host;
}

."$CWD\.appveyor\appveyor.after-build.ps1"

Initialize-KodiRepository;

if ( $Publish.IsPresent ) {
  Push-GHPages -Path "$ENV:APPVEYOR_BUILD_FOLDER\build\"
}

