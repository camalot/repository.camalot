# repository.camalot

[![Build status](https://ci.appveyor.com/api/projects/status/t4kv4mox5koymqq2?svg=true)](https://ci.appveyor.com/project/camalot/repository-camalot)

[Kodi](http://kodi.tv) Addons Repository for Kodi Addons by [camalot](http://github.com/camalot).


----
- [Add Repository to Kodi](#add-repository-to-kodi)
- [Request your addon to be added](#request-your-addon-to-be-added)
- [Build](#build)
- [Configuration](#configuration)
- [Tag and Release Pattern](#tag-and-release-pattern)

----

# Add Repository to Kodi

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

# Request your addon to be added

 - Fork this repository
 - Create a new branch `request/<my-addon-id>` (where `<my-addon-id>` is the id of your addon).
 - Create a _Pull Request_ to the `develop` branch of this repo.

----

# Build

Build is typically handled by CI (Appveyor). The scripts to just 'package' the repository addon is 
`.build/build.msbuild`.

Steps that CI takes is a bit different.

- `.appveyor/appveyor.install.ps1`
  - installs the software needed to build. 
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
  
_NOTE: You need to have your github credentials stored for git._   
    
Then run `.appveyor/appveyor.on-success.ps1` from the root of the project.

```
PS> $ENV:CI_DEPLOY_GITHUB=$true;
PS> $ENV:APPVEYOR_BUILD_FOLDER=".";
PS> ./.appveyor/appveyor.on-success.ps1
```

----
# Configuration

Configuration of what addons are included is set in `.repository.json`.

- `host_url`: The url of the repository
- `plugins`: 
    - `name`: The plugin id
    - `github_url`: This is the clone url for the addon repository
    - `tag_exclude_pattern`: An array of _glob_ style pattern for tags to exclude. Ex: `["*-prerelease"]`
    - `tag_include_pattern`: An array of _glob_ style pattern for tags to include. Default: `["*"]`
    


# Tag and Release Pattern

`[addon.id-][v]<version>`  
The tag/release name can contain the `addon.id`, if it does, it *MUST* have a `-` after it.
Before the `version` you can have an optional `v`. 

Addon packages will be pulled from _Github Releases_ if it can, otherwise, it will use the source and package it up 
as the addon package.
 
To use _Github Releases_, the release name should follow the same pattern as the tags, and the zip file should be
name `<addon.id>-<version>.zip`

---- 

### Notes
 
Originally cloned from [RobLoach's](http://github.com/robloach) 
[repository.robloach ](https://github.com/RobLoach/repository.robloach). 

The original `create_repository.py` script is based off [kodi-create-repo](https://github.com/virajkanwade/kodi-create-repo)
by [Viraj Kanwade](https://github.com/virajkanwade).

