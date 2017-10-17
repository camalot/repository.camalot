# repository.camalot

[![Build status](https://ci.appveyor.com/api/projects/status/iq3374r11951x74p?svg=true)](https://ci.appveyor.com/project/camalot/plugin-repository-camalot)


[Kodi](http://kodi.tv) Addons Repository for Kodi Addons by [camalot](http://github.com/camalot).


----
- [Add Repository to Kodi](#add-repository-to-kodi)

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

 - Fork [repository.camalot](https://github.com/camalot/repository.camalot/)
 - Create a new branch `request/<my-addon-id>` (where `<my-addon-id>` is the id of your addon).
 - Edit `.repository.json` with the information for your addon.
 - Create a _Pull Request_ to the `develop` branch.



