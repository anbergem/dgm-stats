import typing

import requests

from .logging import log


class Api:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_competition(self, id: int) -> typing.Optional[typing.Dict]:
        params = {
            "content": "result",
            "id": id
        }

        result = requests.get(self.base_url, params=params)

        if not result.ok:
            log.warning(f"Could not get competition with id {id}")
            return None

        return result.json()
