from pathlib import Path


class AddonPackage:
    def __init__(self, path, image=None, debug=False):
        self.path = Path(path)
        self.debug = debug
        self.addon_name = self.path.parent.name
        self.image_name = f"{self.addon_name}-package"
        self.image = image
