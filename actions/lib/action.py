from st2common.runners.base_action import Action
from location import Location


class BaseAction(Action):
    def __init__(self, config):
        super(BaseAction, self).__init__(config)
        self._address = self.config["address"]
        self._latitude = self.config["latitude"]
        self._longitude = self.config["longitude"]
        self._timezone = self.config["timezone"]
        self._keys = {
            "google_api_key": self.config["google_api_key"],
            "here_api_key": self.config["here_api_key"],
            "ipgeo_api_key": self.config["ipgeo_api_key"],
        }

        self.location = Location(self._address, self._keys)
