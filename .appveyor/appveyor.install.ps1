& choco install 7zip.commandline -y;
& pip install -r requirements.txt

& git config --global credential.helper store
& git config --global user.email "$($ENV:GITHUB_EMAIL)"
& git config --global user.name "$($ENV:GITHUB_USERNAME)"
Add-Content "$ENV:USERPROFILE\.git-credentials" "https://$($ENV:GITHUB_ACCESS_TOKEN):x-oauth-basic@github.com`n"
