from lib import action


class GetSolarAction(action.BaseAction):
    def run(self):
        return str(self.location.solar())
