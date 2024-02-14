# Personal Minecraft Mod Download

## For Who?

People who have a fixed set of mods that they want to upgrade or downgrade to a specific Minecraft version (like when they play on servers and MultiMC and stuff). If they have 100 mods, they'll have to update 100 of them every time they switch version. This will attempt to alleviate that without the need to use a dedicated software.

## Requirements?

- Python 3.x (stable latest is sufficient)
- Git (optional)
- A familiarity with virtual environment is recommended.

## What?

A short script to download mods from Modrinth (and maybe CurseForge and GitHub in the future?). This will only consist of Fabric mods, but it should be easy to modify it into any mod loaders if you can read the code.

## Why?

1. I'm lazy. And as with all programmers, they'll spend days to automate this process instead of manually doing it.
2. Launcher can be bulky. Something small for a task that's rarely needed is sufficient.

## Features

- [x] Download from Modrinth.
    - [x] Ratelimit
        - It is unclear if their cdn server is also ratelimited.
    - [x] Check for valid mod (check against SHA512 or SHA1).
    - [x] Resolve dependency automatically.
        - This functionality is currently not working as expected (due to the API itself). I will do something about this later.
    - [ ] Download in parallel.
- [ ] Fallback to CurseForge.
- [ ] Fallback to GitHub release download.

## Instruction

The next section will detail how to use the script.

### First Run

1. Download the entire repository via GitHub or Git. 

```sh
git clone https://github.com/MikeJollie2707/personal-mcmod-download.git .
```

2. Install necessary dependencies. If you know how to use `venv`, install there instead. Make sure to activate the environment with `source`.

```sh
python3 -m pip install -r requirements.txt
```

3. Create a `.json` file. The file will have the following structure:

```json
{
    "mod_id": "mod name. This field acts as comment, but don't leave it empty.",
    "mod_id2": "mod name."
}
```

Especially on the FIRST RUN, only include 1-2 mods with close to no dependencies.

You can view the structure in `sample.json`. To find `mod_id` of a mod, find the mod on Modrinth, then scroll down until you see "Project ID" (bottom left of the picture).

![Project ID of Sodium](./assets/where_to_find_modid.png)

4. Run the script. Replace `1.20.4` with the actual Minecraft version and `sample.json` with your file.

```sh
python3 modrinth.py 1.20.4 sample.json
```

In case you did step 2 without using a virtual environment, you can make the script executable like so:

```sh
chmod u+x modrinth.py
./modrinth.py 1.20.4 sample.json
```

### After first run

#### Add more mods

Find them on Modrinth, copy project ID, run the script again, profit. Note that if you have around 100+ mods in a `.json` file, it is recommended to split that into another `.json` file to reduce the load.

#### Custom configuration

See [Settings](#script-settings).

#### Automatically download dependencies

**NOTE: This feature is currently broken.**

See [this setting](#resolve_dependencies). After this, you can remove base mods (like Fabric API) from the `.json` file.

#### Temporarily not download a mod

In the mod remark, set it to empty string, like so:

```json
{
    "mod_id": ""
}
```

## Script Settings

You can manually edit some global variables in `main.py` (all capital letters). **Do not edit any global variables with underscores in front (like `__HEADERS`)**

### `MC_VERSION`

Download mods for this particular version. For snapshots, I don't recommend using this script since 1. Hard to get the snapshot number right and 2. Not many mods will publish for snapshots, so might as well as just do that manually.

Normally, this will take the first command line argument. You can manually set it to a specific value (like in snapshots), but make sure to still provide some dummy value when invoking the script.

### `DOWNLOAD_PATH`

Where the mods will go. By default, it'll go `./download/{MC_VERSION}` (create if not exist). This is usually not necessary to edit since you can copy the mods to the Minecraft instance, but it's there nonetheless.

### `CHECK_HASH`

Whether to verify the integrity of the file you just downloaded. This can help prevent something like `fractureiser` (maybe, it depends on how Modrinth get the public key). By default, this is on, but you can turn it off by setting it to `False`.

### `RESOLVE_DEPENDENCIES`

Big setting. Whether to automatically download all dependencies for a given mod. By default, this is `False`. There are a few things to keep in mind before setting it to `True`:

1. It will only download the first dependency layer. If mod A depends on mod B and C, it'll download mod B and C. However, if mod B also depends on mod D, it *will not* download mod D.
2. If a mod is big (depends on like 50+ mods), it is recommended to put this mod in a separate `.json`.
3. It is very easy to overlook mods that are big with this option on. This is quite a problem if you put many big mods inside one single `.json`. It may cause timeout or some other issues.
4. If you include the dependency mods inside `.json` AND turn this setting on, *whichever entry is closer to the top will be downloaded.* This can cause issues if the parent mod depends on a very specific version of the dependency.

Most of these things are to prevent the script hitting the API ratelimit.

### `VERBOSE_LEVEL`

How noisy the script will be. `logging.ERROR` will only show errors, `logging.WARNING` will show errors and warnings, `logging.INFO` will show `logging.WARNING` and download progress. By default, it is `logging.INFO`, but you can set to `logging.ERROR` if it's spamming a lot.

### `REQUIRE_FEATURED`

Whether to only look for the versions of the mod that's featured. Small setting, but if the script can't find a particular mod for whatever reason, you can try setting this to `False` and see if it picks up. Default to `True`.

### `MOD_LOADER`

Just putting it here in case you download `quilt` or `neoforge`.
