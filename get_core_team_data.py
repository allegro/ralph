import json
import os

import requests
from requests.auth import HTTPBasicAuth

auth = requests.auth.HTTPBasicAuth(
    os.environ['GITHUB_USERNAME'], os.environ['GITHUB_API_KEY']
)
http = requests.Session()


def get_user_info(username):
    url = "https://api.github.com/users/{}".format(username)
    return http.get(url, auth=auth)


if __name__ == "__main__":
    core_team = None
    core_team_with_names = {}
    with open("_data/core_team.json") as f:
        core_team = json.load(f)
    for user in core_team:
        info = get_user_info(user).json()
        core_team_with_names[user] = {
            'name': info['name'],
        }
    with open("_data/core_team_with_names.json", "w") as f:
        json.dump(core_team_with_names, f)
