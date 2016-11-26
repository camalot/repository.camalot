if ( $env:APPVEYOR_REPO_BRANCH -eq "master" ) {
  # $env:CI_DEPLOY_GITHUB = $true;
  [Environment]::SetEnvironmentVariable("CI_DEPLOY_GITHUB", "$true", "Machine")
} elseif ( $env:APPVEYOR_REPO_BRANCH -eq "develop" ) {
  # $env:CI_DEPLOY_GITHUB_PRE = $true;
  # $env:CI_DEPLOY_GITHUB = $false;
  [Environment]::SetEnvironmentVariable("CI_DEPLOY_GITHUB_PRE", "$true", "Machine")
  [Environment]::SetEnvironmentVariable("CI_DEPLOY_GITHUB", "$false", "Machine")
} else {
  [Environment]::SetEnvironmentVariable("CI_DEPLOY_GITHUB_PRE", "$false", "Machine")
  [Environment]::SetEnvironmentVariable("CI_DEPLOY_GITHUB", "$false", "Machine")
}
