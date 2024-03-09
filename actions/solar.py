from lib import action
from lib.location import Location


class GetSolarAction(action.BaseAction):
    def run(self, **parameters):
        self.location = Location([parameters["location"]], self._keys)
        return self.location.solar()
