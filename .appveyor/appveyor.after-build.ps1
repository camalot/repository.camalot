if ( $env:APPVEYOR_REPO_BRANCH -eq "master" -and $ENV:APPVEYOR_PULL_REQUEST_NUMBER -eq "" ) {
  $env:CI_DEPLOY_GITHUB = $true;
} elseif ( $env:APPVEYOR_REPO_BRANCH -eq "develop" ) {
  $env:CI_DEPLOY_GITHUB_PRE = $true;
  $env:CI_DEPLOY_GITHUB = $false;
} else {
  $env:CI_DEPLOY_GITHUB = $false;
}
