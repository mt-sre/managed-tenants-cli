from sretoolbox.binaries import Mtcli, OperatorSDK, Opm

OPERATOR_SDK = OperatorSDK(version="1.4.2", download_path="/tmp")
OPM = Opm(version="1.15.1", download_path="/tmp")
MTCLI = Mtcli(version="0.4.0", download_path="/tmp")
