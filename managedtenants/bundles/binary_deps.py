from sretoolbox.binaries import Mtcli, OperatorSDK, Opm


class LazyBin:
    """
    Abstraction around sretoolbox to avoid pulling binaries from the internet
    before they actually need to be ran.
    """

    def __init__(self, bin_class, version, download_path):
        self.bin_class = bin_class
        self.version = version
        self.download_path = download_path
        self.instance = None

    def run(self, cmd):
        if self.instance is None:
            self.instance = self.bin_class(self.version, self.download_path)

        self.instance.run(*cmd)


OPM = LazyBin(Opm, version="1.24.0", download_path="/tmp")
MTCLI = LazyBin(Mtcli, version="0.10.0", download_path="/tmp")
OPERATOR_SDK = LazyBin(OperatorSDK, version="1.4.2", download_path="/tmp")
