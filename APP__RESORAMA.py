import time
t = str(time.strftime('%Y-%m-%d__%H-%M-%S__%z'))

APP_NAME = "RESORAMA"

import os
import numpy
import cv2 #pip install opencv-python
import configparser
import platform
import psutil
import subprocess
import re
import inspect
import mmap
import numpy as np
from PIL import Image
from pyueye import ueye


# Importing my functions
from FCN__log import log, log_memory_info_verbose
from FCN__time__t36 import t36

# Define a unique string for this runtime as a function of unix time converted to 36-base alphanumeric string
t36 = t36()   

# get the path of this python file
PY_PATH = os.path.abspath(__file__)
PY_NAME = os.path.basename(__file__)
MAIN_PATH = os.path.dirname(PY_PATH)


# Constants for configuration keys, pulled from __config__.ini
## APP
APP_SETTINGS = 'APP_SETTINGS'
ENABLE_LOGGING = 'EnableLogging'
IMAGE_TYPE = 'ImageType'
IMG_DIRECTORY = 'SaveDirectory'
LOG_DIRECTORY = 'LogDirectory'
FILENAME_PREFIX = 'FilenamePrefix'
VERBOSE = 'Verbose'
## CAM
CAM_SETTINGS = 'CAM_SETTINGS'
MODE = 'Mode'
NUM_CAMERAS = 'NumCameras'
SUBSAMPLING = 'Subsampling'
FRAMERATE = 'Framerate'
IS_OSD_ENABLED = 'EnableOSD'
ROTATE_STEPS = 'RotateDegrees'

# define how to load the config file
def app_load_config_ini():
    """
    Load application configurations from config.ini.
    """
    config = configparser.ConfigParser()
    config_path = os.path.join(MAIN_PATH, '__config__.ini')
    
    if not config.read(config_path):
        raise ValueError(f"Failed to read config file at {config_path}")
    
    return config

# load the config file
config = app_load_config_ini()

# APP_SETTINGS
ENABLE_LOGGING = config[APP_SETTINGS]['EnableLogging']
IMG_TYPE = config[APP_SETTINGS][IMAGE_TYPE]
IMG_DIRECTORY = config[APP_SETTINGS][IMG_DIRECTORY]
LOG_DIRECTORY = config[APP_SETTINGS][LOG_DIRECTORY]
FILENAME_PREFIX = config[APP_SETTINGS][FILENAME_PREFIX]
VERBOSE_LEVEL = int(config[APP_SETTINGS][VERBOSE])

# Use unique "t36" string for file naming
LOG_PATH = os.path.join(MAIN_PATH, LOG_DIRECTORY, f"LOG__{t36}.log")
IMG_path = os.path.join(MAIN_PATH, IMG_DIRECTORY, f"IMG__{t36}.png")

# CAM_SETTINGS
MODE = int(config[CAM_SETTINGS][MODE])
NUM_CAMERAS = int(config[CAM_SETTINGS][NUM_CAMERAS])
SUBSAMPLING = int(config[CAM_SETTINGS][SUBSAMPLING])
FRAMERATE = int(config[CAM_SETTINGS][FRAMERATE])
IS_OSD_ENABLED = config[CAM_SETTINGS][IS_OSD_ENABLED]
ROTATE_STEPS = int(int(config[CAM_SETTINGS][ROTATE_STEPS])/90)

# Dictionary to represent relevant settings, for logging
CONFIG_DICT = {
    'MODE' : MODE,
    'NUM_CAMERAS' : NUM_CAMERAS,
    'SUBSAMPLING' : SUBSAMPLING,
    'FRAMERATE' : FRAMERATE,
    'IS_OSD_ENABLED' : IS_OSD_ENABLED,
    'ROTATE_STEPS' : ROTATE_STEPS,
}

# Strings to describe display modes (WIP)
MODES = {
    '1' : "Zoetrope",
    '2' : "Multi-window",
    '3' : "Tiled" #TODO
}

# For debugging and logging purposes only
SYSTEM_INFO = {
    'System': platform.uname().system,
    'Node Name': platform.uname().node,
    'Release': platform.uname().release,
    'Version': platform.uname().version,
    'Machine': platform.uname().machine,
    'Processor (Platform)': platform.uname().processor,
    'Processor (PSUtil)': psutil.cpu_freq().current,
    'Physical Cores': psutil.cpu_count(logical=False),
    'Logical Cores': psutil.cpu_count(logical=True)
}

import socket

# gETTING nETWORK iNFORMATION uSING sOCKET
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

NETWORK_INFO = {
    'Hostname': hostname,
    'IP Address': ip_address,
    'FQDN': socket.getfqdn(),
    # rETRIEVING aLL aVAILABLE iP aDDRESSES fOR tHE cURRENT hOST
    'All IP Addresses': [ip[4][0] for ip in socket.getaddrinfo(hostname, None)]
}


##################################################################################
##################################################################################
##################################################################################
# HELPER FUNCTIONS


def get_mem_address(input):
    return f"Memory address {hex(id(input))}"

# Global variable for performance timer
time_stopwatch_previous = None

# Get "lap" time and reset
def get_stopwatch():
    global time_stopwatch_previous
    
    # gET cURRENT tIME
    time_current = time.time()

    # iF pREVIOUS tIME iS nOT sET, rETURN 0 aND uPDATE tHE pREVIOUS tIME
    if time_stopwatch_previous is None:
        time_stopwatch_previous = time_current
        return 0
    
    # cALCULATE tIME eLAPSED sINCE pREVIOUS cALL
    time_elapsed = time_current - time_stopwatch_previous
    
    # uPDATE tHE pREVIOUS tIME
    time_stopwatch_previous = time_current
    
    return time_elapsed

# Logging function to call stopwatch
def stopwatch(level):
    msg = get_stopwatch()
    if msg != 0:
        log(level, msg)

# cReate dIctionary fRom sTruct
def struct_to_dict(struct):
    result = {}
    for field, _ in struct._fields_:
        value = getattr(struct, field)
        if isinstance(value, bytes):  # cOnvert bYtes tO sTring
            value = value.decode('utf-8').strip('\x00')
        result[field] = value
    return result

# gET mAC aDDRESS fROM iP
def get_mac_address(ip_address):
    if platform.system() == "Windows":
        try:
            # eXECUTE aRP cOMMAND tO gET mAC aDDRESS fROM iP aDDRESS
            cmd_output = subprocess.check_output(["arp", "-a", ip_address]).decode()
            # pARSE mAC aDDRESS
            mac_address = re.search(r"((?:[\da-fA-F]{2}-){5}[\da-fA-F]{2})", cmd_output)
            if mac_address:
                return mac_address.group(0)
        except subprocess.CalledProcessError:
            #print(f"Failed to get MAC for {ip_address}")  # dEBUG mESSAGE
            return None

# gET fRAME iNFO fOR dEBUGGING aND lOGGING
def get_frame_info(variable_name):
    frame = inspect.currentframe()
    try:
        # gOING bACKWARDS oNE fRAME tO gET tHE cALLER's fRAME
        previous_frame = frame.f_back
        if variable_name in previous_frame.f_locals:
            return previous_frame
        else:
            # vARIABLE nOT fOUND iN pREVIOUS fRAME
            return None
    finally:
        # dELETING tHE fRAME oBJECT tO aVOID rEFERENCE cYCLES
        del frame


##################################################################################
##################################################################################
##################################################################################
# BEGINNING UEYE IDS CAMERA SETUP


def initialize_ueye_arrays(data_type, num_items, default=None):
    # cREATING aN aRRAY oF sPECIFIED dATA tYPE fOR nUMBER oF iTEMS sPECIFIED
    return [data_type(default) if default is not None else data_type() for _ in range(num_items)]

# vARIABLES rEGARDING cAMERA oBJECT
CAM = initialize_ueye_arrays(ueye.HIDS, NUM_CAMERAS, default=0)
CAM_sInfo = initialize_ueye_arrays(ueye.SENSORINFO, NUM_CAMERAS)
CAM_cInfo = initialize_ueye_arrays(ueye.CAMINFO, NUM_CAMERAS)
CAM_pcImageMemory = initialize_ueye_arrays(ueye.c_mem_p, NUM_CAMERAS)
CAM_MemID = initialize_ueye_arrays(ueye.int, NUM_CAMERAS)
CAM_rectAOI = ueye.IS_RECT()
CAM_pitch = ueye.INT()
CAM_nBitsPerPixel = ueye.INT(24)    # 24: bITS pER pIXEL fOR cOLOR mODE; tAKE 8 bITS pER pIXEL fOR mONOCHROME
CAM_channels = 3                    # 3: cHANNELS fOR cOLOR mODE(rGB); tAKE 1 cHANNEL fOR mONOCHROME
CAM_m_nColorMode = ueye.INT()		# y8/rGB16/rGB24/rEG32
CAM_bytes_per_pixel = int(CAM_nBitsPerPixel / 8)



##################################################################################
##################################################################################
##################################################################################
# LOGGING AND MAIN APP FUNCTION BEGIN


# Empty stopwatch call to start timer
stopwatch(0)

# Ultra verbose log function if VERBOSE > 9000
# log_memory_info_verbose()

log(0, "---")
log(0, "RUNNING PYTHON FILE")

log(1, f"Time begin: {t}", "⏱️")
log(2, t36, "🔑")

log(1, "Getting system information:", "🖥️")
log(2, "SYSTEM_INFO", "🖥️")
log(2, SYSTEM_INFO, "🖥️")

log(1, "Getting local network information:", "🌐")
log(2, "NETWORK_INFO", "🌐")
log(2, NETWORK_INFO, "🌐")

log(1, f"Running '{APP_NAME}'", "▶️")
log(2, PY_PATH, "🐍")
log(2, PY_NAME, "🐍")

log(1, "---")

def app_initialize_script(main_path="", config_dict={}, log_directory='LOG'):
    log(0, "INITIALIZING SCRIPT", "📃")
    log(1, f"Config file path: {os.path.join(MAIN_PATH, '__config__.ini')}", "⚙️")
    log(2, config_dict)
    log(1, f"Logging to: {main_path}\{log_directory}", "📝")

app_initialize_script(MAIN_PATH, CONFIG_DICT, LOG_DIRECTORY)

log(0, "---")
log(0, "INITIALIZING CAMERAS", "🎥")

# Starts the driver and establishes the connection to the camera
log(1, f"Attempting to initialize {NUM_CAMERAS} camera(s).", "🟡")
num_cams_initialized = 0
for i in range(NUM_CAMERAS):
    log(2, f"Initializing CAM_{i}")
    nRet = ueye.is_InitCamera(CAM[i], None)
    if nRet != ueye.IS_SUCCESS:
        log(3, f"Return code: {nRet}")
        log(3, "ERROR")
    else:
        log(3, "ueye.IS_SUCCESS")   
        #stopwatch(3)
        num_cams_initialized += 1
    log(2, "OK")

log(1, f"Initialized {num_cams_initialized} camera(s) successfully!", "✅")
log(2, "OK")
#stopwatch(2)

NUM_CAMERAS = num_cams_initialized


##################################################################################
##################################################################################
##################################################################################


log(0, "---")
log(0, "GETTING CAMERA INFO", "💫")

# iNITIALIZING eMPTY lIST
# just for logging and user readability
CAM_info_list_dict = []

# Reads out the data hard-coded in the non-volatile camera memory and writes it to the data structure that cInfo points to
for i in range(NUM_CAMERAS):
    # lOGGING mESSAGES
    nRet = ueye.is_GetCameraInfo(CAM[i], CAM_cInfo[i])
    if nRet != ueye.IS_SUCCESS:
        # lOG eRROR mESSAGE
        log(1, f"Return code: {nRet}")
        log(1, "ERROR")
    else:
        log(1, f"CAM_info_list_dict[{i}]", "📜")
        # cONVERT sTRUCT tO dICT aND aPPEND tO lIST
        CAM_info_list_dict.append(struct_to_dict(CAM_cInfo[i]))
        
        cam_id = int(CAM_info_list_dict[i]['Select'])
        ip_address = f"192.168.86.{cam_id+100}"

        CAM_info_list_dict[i]['DevID'] = i+1001

        CAM_info_list_dict[i]['IPaddress'] = ip_address
        CAM_info_list_dict[i]['MACaddress'] = get_mac_address(ip_address)
        log(2, CAM_info_list_dict[i])
log(1, "Acquired info at: CAM_info_list_dict", "📚")
log(2, "OK")


##################################################################################
##################################################################################
##################################################################################


log(0, "SORTING DATA", "🧮")

# sORT tABLE bY sERIAL nUMBER
def sort_table_by_serial(table):
    # sORT uSING sORTED fUNCTION
    sorted_table = sorted(table, key=lambda x: x['SerNo'])
    return sorted_table

# sORT tHE tABLE bY sERIAL nUMBER
CAM_info_list_dict = sort_table_by_serial(CAM_info_list_dict)

log(1, "Sorting CAM_info_list_dict by serial number...", "📥")

# iNITIALIZE eMPTY lISTS aND dICTIONARY
CAM_list_serial = []
CAM_list_cam_id = []
CAM_dict_serial_cam_id = {}
CAM_list_index = []

# lOOP tHROUGH eACH cAMERA tO pOPULATE tHE lISTS aND dICTIONARY
for i in range(NUM_CAMERAS):
    # aDD sERIAL nUMBERS tO lIST
    CAM_list_serial.append(CAM_info_list_dict[i]['SerNo'])
    # aDD cAM iDS tO lIST
    CAM_list_cam_id.append(CAM_info_list_dict[i]['Select'])
    # aDD a kEY vALUE pAIR fOR eACH sErNo : sELECT rESPECTIVELY tO cAM_dict_serial_id
    CAM_dict_serial_cam_id[CAM_info_list_dict[i]['SerNo']] = int(CAM_info_list_dict[i]['Select'])
    # create index list
    CAM_list_index.append(int(CAM_info_list_dict[i]['Select'])-101)
    
log(2, "CAM_dict_serial_cam_id", "📗")
log(3, CAM_dict_serial_cam_id)

log(2, "CAM_list_index", "📜")
log(3, CAM_list_index)

log(1, "OK")


##################################################################################
##################################################################################
##################################################################################


# You can query additional information about the sensor type used in the camera
log(0, "---")
log(0, "GETTING SENSOR INFO", "🩻")

CAM_sensor_info = []


for i in range(NUM_CAMERAS):
    log(1, f"CAM_sensor_info[{i}]")
    nRet = ueye.is_GetSensorInfo(CAM[i], CAM_sInfo[i])
    if nRet != ueye.IS_SUCCESS:
        log(2, "ERROR")
        log(3, f"Return code: {nRet}")
    else:
        # Convert C structure to Python dictionary
        CAM_sensor_info.append(struct_to_dict(CAM_sInfo[i]))
        log(2, CAM_sensor_info[i])
        log(1, "OK")
        #inspect_frame_info = get_frame_info("CAM_sensor_info[i]")
        #log(5, str(inspect_frame_info))


##################################################################################
##################################################################################
##################################################################################

log(0, "---")
log(0, "READYING CAMERAS")

log(1, "Resetting to default.")
for i in range(NUM_CAMERAS):
    nRet = ueye.is_ResetToDefault(CAM[i])
    if nRet != ueye.IS_SUCCESS:
        log(3, "ERROR")
        log(3, f"Return code: {nRet}")
    else:
        log(2, f"Resetting CAM_{i}")
log(1, "OK")


# Set display mode to DIB
log(1, "Setting display mode to DIB.")

for i in range(NUM_CAMERAS):
    #log(2, f"Setting CAM_{i} display")
    nRet = ueye.is_SetDisplayMode(CAM[i], ueye.IS_SET_DM_DIB)
    if nRet != ueye.IS_SUCCESS:
        log(2, "ERROR")
        log(3, f"Return code: {nRet}")
    else:
        log(2, "ueye.is_SetDisplayMode(CAM[i], ueye.IS_SET_DM_DIB)")
        #log(2, "OK")


log(1, "OK")

log(1, "Setting color mode to BAYER.")

def get_frame_info(variable_name):
    frame = inspect.currentframe()
    try:
        # gOING bACKWARDS oNE fRAME tO gET tHE cALLER's fRAME
        previous_frame = frame.f_back
        if variable_name in previous_frame.f_locals:
            return previous_frame
        else:
            # vARIABLE nOT fOUND iN pREVIOUS fRAME
            return None
    finally:
        # dELETING tHE fRAME oBJECT tO aVOID rEFERENCE cYCLES
        del frame

def set_color_mode():
    global CAM
    global CAM_nBitsPerPixel
    global CAM_m_nColorMode
    if int.from_bytes(CAM_sInfo[0].nColorMode.value, byteorder='big') == ueye.IS_COLORMODE_BAYER:
        # setup the color depth to the current windows setting     
        for i in range(NUM_CAMERAS):
            ueye.is_GetColorDepth(CAM[i], CAM_nBitsPerPixel, CAM_m_nColorMode)
            bytes_per_pixel = int(CAM_nBitsPerPixel / 8)
            log(2, f"Setting color mode to CAM_{CAM[i]}")
            dict_color_info = {"IS_COLORMODE_BAYER": True,
                        "m_nColorMode": CAM_m_nColorMode,
                        "nBitsPerPixel": CAM_nBitsPerPixel,
                        "bytes_per_pixel": bytes_per_pixel
                        }
        log(1, "OK")
        log(1, "dict_color_info")
        log(2, dict_color_info)      
        
        #log(2, "OK")

    elif int.from_bytes(CAM_sInfo[0].nColorMode.value, byteorder='big') == ueye.IS_COLORMODE_CBYCRY:
        # for color camera models use RGB32 mode
        CAM_m_nColorMode = ueye.IS_CM_BGRA8_PACKED
        CAM_nBitsPerPixel = ueye.INT(32)
        bytes_per_pixel = int(CAM_nBitsPerPixel / 8)
        
        dict_color_info = {"IS_COLORMODE_CBYCRY": True,
                    "tm_nColorMode": CAM_m_nColorMode,
                    "tnBitsPerPixel": CAM_nBitsPerPixel,
                    "tbytes_per_pixel": bytes_per_pixel
                    }
        log(2, dict_color_info)

    elif int.from_bytes(CAM_sInfo[0].nColorMode.value, byteorder='big') == ueye.IS_COLORMODE_MONOCHROME:
        # for color camera models use RGB32 mode
        CAM_m_nColorMode = ueye.IS_CM_MONO8
        CAM_nBitsPerPixel = ueye.INT(8)
        bytes_per_pixel = int(CAM_nBitsPerPixel / 8)

        dict_color_info = {"IS_COLORMODE_MONOCHROME": True,
                    "tm_nColorMode": CAM_m_nColorMode,
                    "tnBitsPerPixel": CAM_nBitsPerPixel,
                    "tbytes_per_pixel": bytes_per_pixel
                    }
        log(2, dict_color_info)

    else:
        # for monochrome camera models use Y8 mode
        CAM_m_nColorMode = ueye.IS_CM_MONO8
        CAM_nBitsPerPixel = ueye.INT(8)
        bytes_per_pixel = int(CAM_nBitsPerPixel / 8)
        print("else")
    log(1, "OK")
set_color_mode()

# Can be used to set the size and position of an "area of interest"(AOI) within an image
log(1, "Getting full AOI (Area of Interest).")
for i in range(NUM_CAMERAS):
    #log(3, f"CAM_{i}")
    nRet = ueye.is_AOI(CAM[i], ueye.IS_AOI_IMAGE_GET_AOI, CAM_rectAOI, ueye.sizeof(CAM_rectAOI))
    if nRet != ueye.IS_SUCCESS:
        log(2, f"ERROR {nRet}")
    else:
        log(2, f"CAM__{i} AOI:")
        #log(0, str(f"```C\n{rectAOI}\n```"))
        log(3, struct_to_dict(CAM_rectAOI))
log(1, "OK")


##################################################################################
##################################################################################
##################################################################################

log(0, "---")
log(0, "APPLYING SETTINGS", "🔧")

#---------------------------------------------------------------------------------------------------------------------------------------

# Set subsampling for both vertical and horizontal direction
log(1, "Applying subsampling.", "")

for i in range(NUM_CAMERAS):
    if SUBSAMPLING == 1:
        log(2, "Full resolution engaged")
    if SUBSAMPLING == 2:
        nRet = ueye.is_SetSubSampling(CAM[i], ueye.IS_SUBSAMPLING_2X_VERTICAL | ueye.IS_SUBSAMPLING_2X_HORIZONTAL)
    if SUBSAMPLING == 4:
        nRet = ueye.is_SetSubSampling(CAM[i], ueye.IS_SUBSAMPLING_4X_VERTICAL | ueye.IS_SUBSAMPLING_4X_HORIZONTAL)
    if SUBSAMPLING == 8:
        nRet = ueye.is_SetSubSampling(CAM[i], ueye.IS_SUBSAMPLING_8X_VERTICAL | ueye.IS_SUBSAMPLING_8X_HORIZONTAL)
    if nRet != ueye.IS_SUCCESS:
        log(2, f"ERROR{nRet}", "⚠️")
    else:
        log(2, f"CAM_{i} subsampling set to {SUBSAMPLING}X", "✅")
log(1, "OK")

width = CAM_rectAOI.s32Width
height = CAM_rectAOI.s32Height

width_scaled = int(width / SUBSAMPLING)
height_scaled = int(height / SUBSAMPLING)

# Set the new AOI (Area of Interest) with desired width and height
CAM_rectAOI.s32X = ueye.int(0)
CAM_rectAOI.s32Y = ueye.int(0)

CAM_rectAOI.s32Width = ueye.int(width_scaled)
CAM_rectAOI.s32Height = ueye.int(height_scaled)

log(1, "Applying scaled AOI.")
for i in range(NUM_CAMERAS):
    nRet = ueye.is_AOI(CAM[i], ueye.IS_AOI_IMAGE_SET_AOI, CAM_rectAOI, ueye.sizeof(CAM_rectAOI))
    if nRet != ueye.IS_SUCCESS:
        log(2, f"ERROR {nRet}")
    else:
        log(2, f"CAM_{i} AOI set at {SUBSAMPLING}X subsampling.")
        log(3, struct_to_dict(CAM_rectAOI))
log(1, "OK")

log(1, "SETTINGS APPLIED TO CAMERAS")


##################################################################################
##################################################################################
##################################################################################

log(0, "---")
log(0, "ENABLING MEMORY STRUCTURE")

log(1, f"Allocating memory for CAM_pcImageMemory at {get_mem_address(CAM_pcImageMemory[i])}")


# Allocates an image memory for an image having its dimensions defined by width and height and its color depth defined by nBitsPerPixel
for i in range(NUM_CAMERAS):
    nRet = ueye.is_AllocImageMem(CAM[i], width, height, CAM_nBitsPerPixel, CAM_pcImageMemory[i], CAM_MemID[i])
    if nRet != ueye.IS_SUCCESS:
        log(2, "is_AllocImageMem ERROR")
    else:
        # Makes the specified image memory the active memory
        nRet = ueye.is_SetImageMem(CAM[i], CAM_pcImageMemory[i], CAM_MemID[i])
        if nRet != ueye.IS_SUCCESS:
            log(2, f"is_SetImageMem ERROR {nRet}")
        else:
            # Set the desired color mode
            nRet = ueye.is_SetColorMode(CAM[i], CAM_m_nColorMode)
            log(2, f"CAM_pcImageMemory[{i}]")
            log(3, str(CAM_pcImageMemory[i]), "✅")
            log(3, get_mem_address(CAM_pcImageMemory[i]), "✅")
log(1, "OK")

# Activates the camera's live video mode (free run mode)
log(1, "Capturing video data to memory.")
for i in range(NUM_CAMERAS):
    nRet = ueye.is_CaptureVideo(CAM[i], ueye.IS_DONT_WAIT)
    if nRet != ueye.IS_SUCCESS:
        log(2, f"ERROR {nRet}")
    else:
        log(2, f"ueye.is_CaptureVideo(CAM[{i}], ueye.IS_DONT_WAIT)")
log(1, "OK")


log(1, "Enable queue for existing memory sequences.")
for i in range(NUM_CAMERAS):
    # Enables the queue mode for existing image memory sequences
    nRet = ueye.is_InquireImageMem(CAM[i], CAM_pcImageMemory[i], CAM_MemID[i], width, height, CAM_nBitsPerPixel, CAM_pitch)
    if nRet != ueye.IS_SUCCESS:
        log(2, f"ERROR {nRet}")
    else:
        log(2, f"CAM_MemID[{i}] == {str(CAM_MemID[i])}")
log(1, "OK")


##################################################################################
##################################################################################
##################################################################################


log(0, "---")
log(0, "VIDEO STREAM READY", "🚦")


##################################################################################
##################################################################################
##################################################################################

log(0, "---")
log(0, "ACTIVE", "🟢")
log(1, "Configured via __config__.ini", "⚙️")
log(2, CONFIG_DICT)

# cOUNTER tO kEEP tRACK oF wHICH cAMERA tO sHOW nEXT
int_current_frame = 0

# fPS cONFIGURATION
#fps = 12  # 10 fRAMES pER sECOND
wait_time = int(1000 / FRAMERATE)  # tIME iN mS


# fONT cONFIGURATION fOR dISPLAYING cAMERA nUMBER
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 4/SUBSAMPLING
font_color = (255, 255, 255)  # wHITE
font_thickness = 1

log(0, "Press 'Q' to leave the program.")

# iNITIALIZE eMPTY lISTS fOR sTORAGE
CAM_picture_array_list = []
CAM_picture_numpy_list = []

time_video_begin = time.time()
duration_video_uptime = 0

# MAIN VIDEO STREAM LOOP
while(nRet == ueye.IS_SUCCESS):
    if MODE == 1:
        f = CAM_list_index[int_current_frame]
        # gET cURRENT cAMERA iMAGE dATA
        CAM_picture_array = ueye.get_data(CAM_pcImageMemory[f], width, height, CAM_nBitsPerPixel, CAM_pitch, copy=False)

        # rESHAPE tO nUMPY aRRAY
        CAM_bytes_per_pixel = int(CAM_nBitsPerPixel / 8)
        CAM_picture_numpy = numpy.reshape(CAM_picture_array, (height.value, width.value, CAM_bytes_per_pixel))

        if IS_OSD_ENABLED == "True":
            # Create OSD text strings
            OSD_current_time = time.strftime('1%Y%m%d%H%M%S%z')
            OSD_current_frame = f"Frame = {f} / {NUM_CAMERAS}"
            OSD_cam_SerNo = f"Serial: {CAM_info_list_dict[f]['SerNo']}"
            OSD_cam_DevID = f"DevID : {CAM_info_list_dict[f]['DevID']}"
            OSD_cam_CamID = f"CamID : {CAM_info_list_dict[f]['Select']}"
            
            # Add  OSD text strings to image array
            cv2.putText(CAM_picture_numpy, OSD_current_time, (8, 32), cv2.FONT_HERSHEY_PLAIN, font_scale, font_color, font_thickness)
            cv2.putText(CAM_picture_numpy, OSD_current_frame, (8, 64), cv2.FONT_HERSHEY_PLAIN, font_scale, font_color, font_thickness)
            cv2.putText(CAM_picture_numpy, OSD_cam_SerNo, (8, 96), cv2.FONT_HERSHEY_PLAIN, font_scale, font_color, font_thickness)
            cv2.putText(CAM_picture_numpy, OSD_cam_DevID, (8, 128), cv2.FONT_HERSHEY_PLAIN, font_scale, font_color, font_thickness)
            cv2.putText(CAM_picture_numpy, OSD_cam_CamID, (8, 160), cv2.FONT_HERSHEY_PLAIN, font_scale, font_color, font_thickness)
            

        # Rotate the frame if specified in config file
        if ROTATE_STEPS != 0:
            CAM_picture_numpy = numpy.rot90(CAM_picture_numpy, k=ROTATE_STEPS, axes=(0, 1))

        # Create a window to show the image
        cv2.imshow(PY_NAME, CAM_picture_numpy)

        # sERIALIZE tO bYTE aRRAY
        serialized_data = CAM_picture_numpy.tobytes()

        # cREATE sHARED mEMORY uSING mmap
        with mmap.mmap(-1, len(serialized_data), tagname="RESORAMA", access=mmap.ACCESS_WRITE) as mm:
            mm.write(serialized_data)

    if MODE == 2:       
        # lOOP oVER aLL cAMERAS
        for i, idx in enumerate(CAM_list_index):

            # gET cURRENT cAMERA iMAGE dATA
            CAM_picture_array = ueye.get_data(CAM_pcImageMemory[idx], width, height, CAM_nBitsPerPixel, CAM_pitch, copy=False)

            # rESHAPE tO nUMPY aRRAY
            CAM_bytes_per_pixel = int(CAM_nBitsPerPixel / 8)
            CAM_picture_numpy = np.reshape(CAM_picture_array, (height.value, width.value, CAM_bytes_per_pixel))
            
            if IS_OSD_ENABLED == "True":
                # Create OSD text strings
                OSD_current_time = time.strftime('1%Y%m%d%H%M%S%z')
                OSD_current_frame = f"Frame = {i} / {NUM_CAMERAS}"
                OSD_cam_SerNo = f"Serial: {CAM_info_list_dict[i]['SerNo']}"
                OSD_cam_DevID = f"DevID : {CAM_info_list_dict[i]['DevID']}"
                OSD_cam_CamID = f"CamID : {CAM_info_list_dict[i]['Select']}"
                
                # Add  OSD text strings to image array
                cv2.putText(CAM_picture_numpy, OSD_current_time, (8, 32), cv2.FONT_HERSHEY_PLAIN, font_scale, font_color, font_thickness)
                cv2.putText(CAM_picture_numpy, OSD_current_frame, (8, 64), cv2.FONT_HERSHEY_PLAIN, font_scale, font_color, font_thickness)
                cv2.putText(CAM_picture_numpy, OSD_cam_SerNo, (8, 96), cv2.FONT_HERSHEY_PLAIN, font_scale, font_color, font_thickness)
                cv2.putText(CAM_picture_numpy, OSD_cam_DevID, (8, 128), cv2.FONT_HERSHEY_PLAIN, font_scale, font_color, font_thickness)
                cv2.putText(CAM_picture_numpy, OSD_cam_CamID, (8, 160), cv2.FONT_HERSHEY_PLAIN, font_scale, font_color, font_thickness)

            # sERIALIZE tO bYTE aRRAY
            serialized_data = CAM_picture_numpy.tobytes()

            # cREATE sHARED mEMORY uSING mmap
            tagname = f"{CAM_info_list_dict[i]['SerNo']}"
            with mmap.mmap(-1, len(serialized_data), tagname=tagname, access=mmap.ACCESS_WRITE) as mm:
                mm.write(serialized_data)

            # dISPLAY eACH iMAGE iN a sEPARATE wINDOW
            cv2.imshow(f"{PY_NAME}_{i} - CAM_info_list_dict[i]['SerNo']", CAM_picture_numpy)

        

    if MODE == 3:
        True







    # pRESS 'q' tO eXIT
    if cv2.waitKey(wait_time) & 0xFF == ord('q'):
        MODE = 0
        duration_video_uptime = time.time() - time_video_begin
        break

    # iNCREMENT tHE cOUNTER aND wRAP aROUND iF nECESSARY
    int_current_frame = (int_current_frame + 1) % len(CAM_list_index)

log(0, "---")
log(0, "EXITING CAMERA", "❌")
log(1, f"Video was live for {duration_video_uptime} seconds")

log(1, "Capturing one more frame for logging purposes.")
# One more frame for logging purposes
CAM_picture_array = ueye.get_data(CAM_pcImageMemory[0], width, height, CAM_nBitsPerPixel, CAM_pitch, copy=False)

# ...reshape it in an numpy array...
CAM_bytes_per_pixel = int(CAM_nBitsPerPixel / 8)
CAM_picture_numpy = numpy.reshape(CAM_picture_array,(height.value, width.value, CAM_bytes_per_pixel))

# Save the last frame as a BMP image file using PIL
str_img_path = os.path.join(MAIN_PATH, IMG_DIRECTORY, f"IMG__{time.strftime('1%Y%m%d%H%M%S%z')}.bmp")
img_pil = Image.fromarray(CAM_picture_numpy)
img_pil.save(str_img_path)

log(2, str_img_path, "🖼️")
log(2, "Image saved as BMP using PIL", "🖼️")
log(2, f"File size: {os.path.getsize(str_img_path)/(1024*1024)} MB", "📂")

# Releases an image memory that was allocated using is_AllocImageMem() and removes it from the driver management
log(1, "Releasing camera feed image memory.")
for i in range(NUM_CAMERAS):
    log(2, f"Freeing image for CAM_{i}", "⏏️")
    log(3, get_mem_address(CAM_pcImageMemory[i]), "♻️")
    ueye.is_FreeImageMem(CAM[i], CAM_pcImageMemory[i], CAM_MemID[i])

# Disables the hCam camera handle and releases the data structures and memory areas taken up by the uEye camera
log(1, "Disabling cameras.")
for i in range(NUM_CAMERAS):
    log(2, f"Disabling CAM_{i}", "❌")
    ueye.is_ExitCamera(CAM[i])

# Destroys the OpenCv windows
log(1, "Closing viewer window.")
log(2, get_mem_address(cv2),"♻️")
cv2.destroyAllWindows()



log(0, "COMPLETE")

dict_session_info = {
    'COMPUTER' : SYSTEM_INFO["Node Name"],
    'T36 ID' : t36,
    'MAC ADDR' : "#TODO add mac address",
    'IP ADDR' : "#TODO add network info",
    
    'duration' : duration_video_uptime
    
}

log(1, "dict_session_info")
log(1, dict_session_info)

# TODO save file to Azure or OneDrive using unique ID string
# TODO