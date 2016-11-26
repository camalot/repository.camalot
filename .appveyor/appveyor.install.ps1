(& choco install 7zip.commandline -y);

if ( $LASTEXITCODE -ne 0 ) {
    exit $LASTEXITCODE;
}

(& pip install -r .requirements.txt);

if ( $LASTEXITCODE -ne 0 ) {
    exit $LASTEXITCODE;
}
