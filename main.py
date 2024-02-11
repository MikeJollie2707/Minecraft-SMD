import requests

MODS = ["Fabric API"]

__HEADERS = {
    "User-Agent": "MikeJollie2707/personal-mcmod-download/0.0.1",
}
__MODRINTH_BASE_DEV_API = "https://staging-api.modrinth.com/v2"
__MODRINTH_BASE_PROD_API = "https://api.modrinth.com/v2"

if __name__ == "__main__":
    with requests.Session() as conn:
        conn.headers.update(__HEADERS)
        for mod in MODS:
            print(mod)

            res: requests.Response = conn.get(
                f"{__MODRINTH_BASE_DEV_API}/search",
                params={
                    "query": mod,
                    # Hack + temporary way to do this. Will find a proper lib later.
                    "facets": str([["categories:fabric"], ["versions:1.20.2"]]).replace(
                        "'", '"'
                    ),
                },
            )

            print(res.status_code)
            # print(res.json())

            data = res.json()
            project = data["hits"][0]
            project_id = project["project_id"]

            print(project_id)

            res = conn.get(
                f"{__MODRINTH_BASE_DEV_API}/project/{project_id}/version",
                # Apparently it still returns non-featured version which is bruh.
                params={"loaders": ["fabric"], "game_versions": ["1.20.2"], "featured": "true"},
            )

            print(res.status_code)
            print(res.json())
