"""
Initial configuration for new downloads and updates
"""
import appdirs

deneyapKart = "dydk_mpv10"
deneyapMini = "dym_mpv10"
deneyapKart1A = "dydk1a_mpv10"
deneyapKartG = "dyg_mpv10"

AGENT_VERSION = "1.0.1"
DENEYAP_VERSION = "1.3.8"
TEMP_PATH = f"{appdirs.user_data_dir()}\DeneyapKartWeb\Temp"
CONFIG_PATH = f"{appdirs.user_data_dir()}\DeneyapKartWeb"
LOG_PATH = f"{appdirs.user_data_dir()}\DeneyapKartWeb"
LIB_PATH = f"{appdirs.user_data_dir()}/DeneyapKartWeb/packages/deneyap/hardware/esp32/{DENEYAP_VERSION}/libraries"
