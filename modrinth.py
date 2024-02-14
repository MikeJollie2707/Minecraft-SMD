#!/usr/bin/python3

import hashlib
import json
import logging
import os
import sys

import requests

# The version of Minecraft. For snapshots versions, look on Modrinth docs.
# This will be used in several places in the script so make sure this is correct.
MC_VERSION = sys.argv[1]

# The destination for the mods.
DOWNLOAD_PATH = os.path.join("download", MC_VERSION)

# Whether to verify the integrity of the mod file. False make the process faster but might be LESS SECURE.
CHECK_HASH = True

# Whether to automatically download required dependencies. False will not download a mod required dependencies.
# NOTE: This will only resolve 1 level of dependency. If the dependency also depends on another dependencies, list the 2nd
# level mods in the .json
# NOTE: Enable this to true can make you reach timeout if you're not careful of which mods you're downloading.
RESOLVE_DEPENDENCIES = False

# How noisy the script will be.
# logging.INFO will be somewhat noisy, but it'll show download progress.
# logging.WARNING will only show warning and errors.
VERBOSE_LEVEL = logging.INFO

# Whether to only look at featured versions. False might return duplicate mod entries.
# A notorious example for now that has other versions not featured is Carpet.
REQUIRE_FEATURED = True

# Note that I don't test any other loaders aside from Fabric, but theoretically it should work for others.
MOD_LOADER = "fabric"

# Don't change any of these.
__HEADERS = {
    "User-Agent": "MikeJollie2707/personal-mcmod-download/0.0.1",
}
__MODRINTH_BASE_DEV_API = "https://staging-api.modrinth.com/v2"
__MODRINTH_BASE_PROD_API = "https://api.modrinth.com/v2"
__TESTING = False
logging.basicConfig(level=VERBOSE_LEVEL)


class RequestController:
    __request_count = 0

    def __init__(self):
        self.__test_api = "https://staging-api.modrinth.com/v2"
        self.__prod_api = "https://api.modrinth.com/v2"

    def get(self, conn: requests.Session, endpoint, **kwargs):
        if RequestController.__request_count >= 200:
            raise RuntimeError(
                "This script made 200+ requests to the API. For safety, it'll terminate. Do NOT run the script again for the next 2 minutes."
            )

        url = self.__prod_api
        if kwargs.get("test"):
            url = self.__test_api
        del kwargs["test"]

        RequestController.__request_count += 1
        return conn.get(url + endpoint, **kwargs)


# https://www.programiz.com/python-programming/examples/hash-file
def hash_file(filename):
    """This function returns the SHA-1 hash
    of the file passed into it"""

    # make a hash object
    h = hashlib.sha1()

    # open file for reading in binary mode
    with open(filename, "rb") as file:
        # loop till the end of the file
        chunk = 0
        while chunk != b"":
            # read only 1024 bytes at a time
            chunk = file.read(1024)
            h.update(chunk)

    # return the hex representation of digest
    return h.hexdigest()


def to_list_param(l: list, /) -> str:
    """Modrinth parameters often need like params1=["some","thing"],
    which is not possible for requests to format."""
    return str(l).replace("'", '"')


if __name__ == "__main__":
    if len(sys.argv) == 3:
        mod_file = sys.argv[2]
    else:
        print("Missing a command line argument. Need to be .json")
        exit(1)

    mods = {}
    with open(mod_file, "r", encoding="utf-8") as fin:
        mods = json.load(fin)

    with requests.Session() as conn:
        conn.headers.update(__HEADERS)
        ctrl = RequestController()

        for mod_id, mod_remark in mods.items():
            if not mod_remark:
                logging.warning("Mod id %s has Falsy value. Skipping...", mod_id)
                continue

            res = ctrl.get(
                conn,
                f"/project/{mod_id}/version",
                params={
                    "loaders": to_list_param([MOD_LOADER]),
                    "game_versions": to_list_param([MC_VERSION]),
                    "featured": "true" if REQUIRE_FEATURED else "false",
                },
                test=__TESTING,
            )

            if res.status_code != 200:
                logging.error(
                    "Mod id %s (%s) can't be found. Make sure it is correct.",
                    mod_id,
                    mod_remark,
                )
                logging.debug(res.text)
                continue

            mod_version = res.json()
            if not mod_version:
                logging.error(
                    "Mod id %s (%s) doesn't have version %s. Make sure it is correct.",
                    mod_id,
                    mod_remark,
                    MC_VERSION,
                )
                continue

            # Resolve dependency.
            # The Version object has a "dependencies" field, which contains version ID and proj ID.
            # An easy way would be to modify mods to include this new field (or edit existing one to avoid duplication).
            # However, in a rare case where the version required is super specific, this'll likely break.

            files = mod_version[0]["files"]
            dependencies = mod_version[0]["dependencies"]

            for file in files:
                if file["primary"]:
                    dl_url = file["url"]
                    filename = file["filename"]
                    sha1 = file["hashes"]["sha1"]

                    logging.info(f"Downloading {filename}...")

                    dl_resp = requests.get(
                        dl_url
                    )  # Don't use session, it's different host.

                    if dl_resp.status_code != 200:
                        logging.error("Failed to download %s", filename)
                        continue

                    if not os.path.exists(DOWNLOAD_PATH):
                        os.makedirs(DOWNLOAD_PATH)

                    with open(os.path.join(DOWNLOAD_PATH, filename), "wb") as fout:
                        fout.write(dl_resp.content)

                    if (
                        CHECK_HASH
                        and hash_file(os.path.join(DOWNLOAD_PATH, filename)) != sha1
                    ):
                        logging.error(
                            "Content of %s doesn't match. Highly recommend to delete this file.",
                            filename,
                        )
                        break

                    logging.info("Checksum okay.")

                    if RESOLVE_DEPENDENCIES:
                        depend_ids = []
                        for dependency in dependencies:
                            if dependency["project_id"] in mods:
                                logging.warning(
                                    "Dependency %s for %s already available in .json. Skipping...",
                                    dependency["project_id"],
                                    mod_id,
                                )
                                continue

                            if dependency["dependency_type"] != "required":
                                continue

                            if not dependency["version_id"]:
                                logging.error(
                                    "Dependency %s is required, but API doesn't return a valid version_id. Skipping...",
                                    dependency["project_id"],
                                )
                                continue

                            depend_ids.append(dependency["version_id"])

                        if not depend_ids:
                            continue

                        logging.info("Getting dependency for %s...", mod_id)
                        res: requests.Response = ctrl.get(
                            conn,
                            "/versions",
                            params=None
                            if not depend_ids
                            else {"ids": to_list_param(depend_ids)},
                            test=__TESTING,
                        )

                        if res.status_code != 200:
                            logging.error(
                                "Can't get dependencies for %s. Skipping...", mod_id
                            )
                            continue

                        # Recursive part. Manually do this to keep it 1 level.
                        versions = res.json()
                        for version in versions:
                            _files = version["files"]
                            for f in _files:
                                if f["primary"]:
                                    _dl_url = f["url"]
                                    _filename = f["filename"]
                                    _sha1 = f["hashes"]["sha1"]

                                    logging.info("Downloading %s...", _filename)

                                    dl_resp = requests.get(
                                        _dl_url
                                    )  # Don't use session, it's different host.

                                    if dl_resp.status_code != 200:
                                        logging.error(
                                            "Failed to download %s.", _filename
                                        )
                                        continue

                                    if not os.path.exists(DOWNLOAD_PATH):
                                        os.makedirs(DOWNLOAD_PATH)

                                    with open(
                                        os.path.join(DOWNLOAD_PATH, _filename), "wb"
                                    ) as fout:
                                        fout.write(dl_resp.content)

                                    if (
                                        CHECK_HASH
                                        and hash_file(
                                            os.path.join(DOWNLOAD_PATH, _filename)
                                        )
                                        != _sha1
                                    ):
                                        logging.error(
                                            "Content of %s doesn't match. Highly recommend to delete this file.",
                                            _filename,
                                        )
                                        break

                                    logging.info("Checksum okay.")
