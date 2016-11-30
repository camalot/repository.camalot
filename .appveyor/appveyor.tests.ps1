$testResults = (& python -m unittest discover -v -s tests -p *.py *>&1);
if ($LASTEXITCODE -ne 0) {
    $testResults | Write-Error;
    exit $LASTEXITCODE;
} else {
    $testResults | Write-Host;
}