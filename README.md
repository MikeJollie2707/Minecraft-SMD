Will tailor this README to make it look more formal later cuz I ain't got no time.


## What?

A short script to download mods from Modrinth (and maybe CurseForge in the future?). This will only consist of Fabric mods, but it should be easy to modify it into any mod loaders if you can read the code.

## Why?

1. I'm lazy. And as with all programmers, they'll spend days to automate this process instead of manually doing it.
2. Launcher is bulky and it's a software, which is ugh. I just need a script to do this.

## Features

- [ ] Download from Modrinth.
    - [ ] Check for valid mod (check against SHA512).
    - [ ] Resolve dependency automatically.
- [ ] Fallback to CurseForge.
- [ ] Fallback to GitHub release download.
- [ ] Maybe make a Bash version (big if).

## Structure

Just laying out here cuz I don't have anywhere else to put yet.

- A file to contain mod names (Modrinth call them project). Probably a json.
- Use [`GET /search`](https://docs.modrinth.com/#tag/projects) to find mods. The `query` and `facets` in particular are relevant. `limit` can also be used.
- Use [`GET /project/{project_id}/version`](https://docs.modrinth.com/#tag/versions/operation/getProjectVersions) to get mod versions. This endpoint accept 2 noteworthy params: `loaders` and `game_versions`. A noteworthy attr from the response is the `files`, which contains everything we want from download url to hash.
- Check the hash, use GET on the cdn url. Do that for the rest of the mods. Profit.
