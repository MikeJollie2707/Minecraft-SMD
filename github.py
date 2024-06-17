import json
import logging
import os
import sys

import requests

DEFAULT_DEPTH = 10
MAX_DEPTH = 30

__HEADERS = {"Accept": "application/vnd.github+json"}
__BASE_URL = "https://api.github.com/repos"
logging.basicConfig(level="INFO")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        mod_file = sys.argv[1]
    else:
        print("Missing a command line argument. Need to be .json")
        sys.exit(1)
    
    settings: dict = {}
    mod_list: dict[str, list[str]] = {}
    with open(mod_file) as fin:
        try:
            settings = json.load(fin)
            depth = settings.get("SEARCH_DEPTH")
            if not depth:
                depth = DEFAULT_DEPTH

            depth = min(depth, MAX_DEPTH)

            keywords = settings["KEYWORDS"]
            raw_dl_path = settings["DOWNLOAD_PATH"]
            download_path = os.path.join(*raw_dl_path)
            mod_list = settings["MODS"]
        except Exception as e:
            print(e)
            sys.exit(1)

    with requests.Session() as conn:
        conn.headers.update(__HEADERS)

        for mod_author, mods in mod_list.items():
            for mod in mods:
                res = conn.get(
                    __BASE_URL + f"/{mod_author}/{mod}/releases",
                    params={"per_page": depth},
                )

                if res.status_code != 200:
                    logging.error(
                        "'%s' by %s repository can't be found. Check the spelling.",
                        mod,
                        mod_author,
                    )
                    logging.debug(res.text)
                    continue

                releases = res.json()
                is_downloaded = False
                for release in releases:
                    assets = release["assets"]
                    for asset in assets:
                        if ".jar" in asset["name"] and all(
                            [kw in asset["name"] for kw in keywords]
                        ):
                            logging.info(f"Downloading {asset['name']}...")
                            dl_resp = conn.get(asset["browser_download_url"])

                            if dl_resp.status_code != 200:
                                logging.error("Failed to download %s", asset["name"])
                                continue

                            if not os.path.exists(download_path):
                                os.makedirs(download_path)

                            with open(
                                os.path.join(download_path, asset["name"]), "wb"
                            ) as fout:
                                fout.write(dl_resp.content)
                                is_downloaded = True

                            # Download only one .jar file.
                            if is_downloaded:
                                break

                    # Don't break here cuz maybe multiple versions of mods on same version.

                if not is_downloaded:
                    logging.error(
                        "'%s' by %s can't be downloaded. Check keywords and search depth.",
                        mod,
                        mod_author,
                    )
                    continue
