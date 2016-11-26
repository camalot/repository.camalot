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

``` bash
python create_repository.py && ./update-directory-index.sh && ./push-gh-pages.sh build
```

# kodi-create-repo
Helper script to put together a Kodi repo for your plugins

**REQUIREMENTS:**
- Install lxml and GitPython. ``` pip install -r requirements.txt ```

**CONFIG:**
- Create a copy of ```config.json.sample``` and name it ```config.json```
- Edit config.json to set the correct values.

**RUN:**
- ```python create_repository.py```
- ```python create_repository.py --gh-pages``` *Will generate directory listing index pages for upload to github repo with gh-pages.*

**OUTPUT:**
- The repo structure files are stored in build directory

**NOTE:**
- Currently supports only addons available in github
- Uses tags for version number

**THANKS:**
- Special thanks to [Simple Core](https://www.youtube.com/channel/UCgC_gjO6044hDD6RRm5o7Iw)  
[![](http://img.youtube.com/vi/zm1pvAt5uvU/mqdefault.jpg)](https://www.youtube.com/watch?v=zm1pvAt5uvU)

**TODO:**
- Handle addon update
- Handle separate kodi version for addons and repo structure
- FTP upload
