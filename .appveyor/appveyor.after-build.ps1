if ( $env:APPVEYOR_REPO_BRANCH -eq "master" -and ($env:APPVEYOR_PULL_REQUEST_NUMBER -eq $null -or $env:APPVEYOR_PULL_REQUEST_NUMBER == "") ) {
  $env:CI_DEPLOY_GITHUB = $true;
  $env:CI_DEPLOY_GITHUB_PRE = $false;
} elseif ( $env:APPVEYOR_REPO_BRANCH -eq "develop" ) {
  $env:CI_DEPLOY_GITHUB_PRE = $true;
  $env:CI_DEPLOY_GITHUB = $false;
} else {
  $env:CI_DEPLOY_GITHUB_PRE = $false;
  $env:CI_DEPLOY_GITHUB = $false;
}



function Push-GHPages {
  param (
    [Parameter(Mandatory=$true)]
    [ValidateScript({ Test-Path -Path $_ -PathType 'Container'})]
    [String] $Path
  )
  begin {
    $remote = (& git config remote.origin.url);
    $described_rev = (& git rev-parse HEAD | git name-rev --stdin);
    $cwd = Get-Location;
  }
  process {
    Set-GitCredentials;
    Set-Location -Path $Path;
    $cdup = (& git rev-parse --show-cdup)
    if ( $cdup -ne '' ) {
      (& git init);
      (& git remote add --fetch origin "$remote");
    }
    (& git rev-parse --verify origin/gh-pages 2>&1) | Out-Null;
    $verify_origin = $LASTEXITCODE;
    if ( $verify_origin -eq 0 ) {
      (& git symbolic-ref HEAD refs/heads/gh-pages);
    } else {
      (& git checkout --orphan gh-pages);
    }

    (& git add -A);
    (& git commit -m "pages built at $described_rev");
    (& git push origin gh-pages -f);

    Set-Location -Path $cwd;
  }
}

function Initialize-KodiRepository {
  param()
  begin {}
  process {
    (& python ./.build/create_repository.py);
    if ( $LASTEXITCODE -ne 0 ) {
        exit $LASTEXITCODE;
    }
  }
}

function Set-GitCredentials {
    param()
    begin{}
    process {
        if ($ENV:GITHUB_ACCESS_TOKEN -ne '' -and $ENV:GITHUB_EMAIL -ne '' -and $ENV:GITHUB_USERNAME -ne '' -and $ENV:CI -eq $true) {
            & git config --global credential.helper store
            & git config --global user.email "$($ENV:GITHUB_EMAIL)"
            & git config --global user.name "$($ENV:GITHUB_USERNAME)"
            Add-Content "$ENV:USERPROFILE\.git-credentials" "https://$($ENV:GITHUB_ACCESS_TOKEN):x-oauth-basic@github.com`n"
        }
    }
}


if ( $env:CI_DEPLOY_GITHUB -eq $true ) {
  Initialize-KodiRepository;
  Push-GHPages -Path "$ENV:APPVEYOR_BUILD_FOLDER\build\"
} else {
    if ( $env:CI -eq $true ) {
        "Not Pushing GH-PAGES because ENV:CI_DEPLOY_GITHUB is '$ENV:CI_DEPLOY_GITHUB'." | Write-Warning;
    }
}