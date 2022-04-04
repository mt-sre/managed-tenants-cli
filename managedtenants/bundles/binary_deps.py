from sretoolbox.binaries import Mtcli, OperatorSDK, Opm

OPM = Opm(version="1.19.5", download_path="/tmp")
MTCLI = Mtcli(version="0.10.0", download_path="/tmp")
OPERATOR_SDK = OperatorSDK(version="1.4.2", download_path="/tmp")
