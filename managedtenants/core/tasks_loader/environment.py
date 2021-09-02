from managedtenants.data.environments import ENVIRONMENTS


class Environment:
    def __init__(self, environment, args):
        self.name = environment
        self.ocm_api_insecure = args.ocm_api_insecure
        if args.ocm_api:
            self.ocm_api = args.ocm_api
        else:
            self.ocm_api = ENVIRONMENTS[self.name]["ocm_api"]

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.name)})"
