# repository.camalot

[Kodi](http://kodi.tv) Addons Repository for Kodi Addons by [camalot](http://github.com/camalot).

Cloned from [RobLoach's](http://github.com/robloach) [repository.robloach ](https://github.com/RobLoach/repository.robloach). The repository itself built with [kodi-create-repo](https://github.com/virajkanwade/kodi-create-repo), by [Viraj Kanwade](https://github.com/virajkanwade).

----

## Add Repository to Kodi

- Navigate to `System -> File Manager`
- Open file browser and click on `Add Source`
- For the path, enter: `https://camalot.github.io/repository.camalot/`
- For the name, enter: `camalot-repo`  
  [![Add Repo](http://i.imgur.com/JtKm9kXl.png)](http://i.imgur.com/JtKm9kX.png)
  
--- 
  
- Next, go to `System -> Add-ons`
- Click on `Install from zip file`
- Navigate to `camalot-repo/repository.camalot-1.0/repository.camalot-1.0.zip`
- Click `OK`

---
- Now back to `System -> Add-ons`
- Click on `Install from repository`
- Select `camalot's Addons` and browse the addons


----
## Build

Build is typically handled by CI (Appveyor). The scripts to just 'package' the repository addon is 
`.build/build.msbuild`.

Steps that CI takes is a bit different.

- `.appveyor/appveyor.install.ps1`
  - installs the software needed to build. 
  - **DO NOT** run locally, it sets git credentials, it will set them blank because the 
  environment variables are not defined.
- `.appveyor/appveyor.before-build.ps1`
  - preps things before building
- `.build/build.msbuild`
  - performs the packaging / build of the repository addon.
- `.build/CIProperties.msbuild`
  - this is included by `.build/build.msbuild`. it sets values that are used by `.build/build.msbuild`,
  and has `defaults` so the build script can be executed locally.
- `.appveyor/appveyor.after-build.ps1`
  - sets some env variables for where we are deploying, dependant upon the branch.
- `.appveyor/appveyor.tests.ps1` 
  - execute some tests
- `.appveyor/appveyor.before-packaging.ps1`
  - currently nothing
- `.appveyor/appveyor.before-deployment.ps1`
  - currently nothing
- `.appveyor/appveyor.after-deployment.ps1`
  - currently nothing
- `.appveyor/appveyor.on-success.ps1`
  - if the build and deployment was successful, it will generate the repository and then
  publish it to the gh-pages branch.
  
To run a `local` build of the repo and publish it to `gh-pages` you will need to set the following environment 
variables:

- `$ENV:CI_DEPLOY_GITHUB=$true`  
- `$ENV:APPVEYOR_BUILD_FOLDER="."` 
  - This is the working directory, which should be the root of the project.
       
Then run `.appveyor/appveyor.on-success.ps1` from the root of the project

```
PS> $ENV:CI_DEPLOY_GITHUB=$true;
PS> $ENV:APPVEYOR_BUILD_FOLDER=".";
PS> ./.appveyor/appveyor.on-success.ps1
```

----
## Configuration

Configuration of what addons are included is set in `.repository.json`.

- `host_url`: The url of the repository