# Zombuild

Simple build tools for Project Zomboid mods.

Configured by a `zombuild.json` file in your project root.

```json
{
    "$schema": "./zombuild.schema.json",

    "id": "mymod",
    "name": "My Mod's Workshop Name",
    "version": "0.0.1",
    "url": "https://example.com",
    "description": { "ref": "mod-description.txt" },
    "authors": [ "Alan Turing" ],

    "preview": "assets/preview.png",

    "category": "features",
    "require": [ "my_other_mod" ],
    "incompatible": [  ],


    "mods": {
        "mymod": {
            "name": "My Mod's In-Game Name",
            "poster": "assets/poster.png",
            "icon": "assets/icon.png",
            "versionMin": "42.16",
            "versions": {
                "common": {
                    "source": "assets/textures",
                    "prefix": "media/textures/mymod"
                },

                "42.16": [
                    {
                        "source": "mods/main/latest/media",
                        "prefix": "media",
                        "ignore": "*.d.lua"
                    },
                    {
                        "source": "mods/main/latest/translations",
                        "prefix": "media/lua/shared/Translate",
                        "glob": "*.json"
                    }
                ]
            },
            "require": [ ],
            "incompatible": [ ],
        },
    },

    "plugins": [ "core", "codegen" ],

    "tasks": {
        
    }
}
```

Generates the appropriate mod structure and mod.info files based on the metadata from the project file.

Some mod.info fields may be set on either the top level object or the mod object, with values from the mod object taking precedence.

The tool can be expanded via a plugin system. Check out `zombuild_codegen/` for an example of a single-file plugin.

## Building 

Requires Python 3.14

```
> python --version
Python 3.14.3
```

If Python 3.14 is your global python, `build.bat` should be able to take care of the entire build process on Windows. Failing that:

In a virtual environment:

```
python -m pip install setuptools build
python -m build
```

## Usage

As this tool is currently in alpha, it is not available on PyPI. It must be manually cloned and built locally. Documentation will be improved as the tool matures.


I suggest creating a virtual environment in your mod project's root folder, then installing your locally-built copy of zombuild there via:

```
python -m pip install /path/to/zombuild
```

You can then invoke zombuild from that virtual environment:

```
zombuild -h
zombuild list
zombuild run clean build
```