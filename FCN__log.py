import os
from prettytable import PrettyTable
import logging
import time
import configparser
import inspect

# Importing my functions
from FCN__time__t36 import t36

T36 = t36()

# get the path of this python file
PY = os.path.abspath(__file__)

# main path to pull config file from, also basis for IMG and LOG folders
MAIN_PATH = os.path.dirname(PY)

# begin stopwatch for performance tracking
start_time = time.perf_counter()
perf_counter_stop = 0
def perf_timer():
    elapsed_time = time.perf_counter() - start_time
    return f"{elapsed_time:.10f}"

# Constants for configuration keys, pulled from __config.ini
APP_SETTINGS = 'APP_SETTINGS'
ENABLE_LOGGING = 'EnableLogging'
IMAGE_TYPE = 'ImageType'
IMG_DIRECTORY = 'SaveDirectory'
LOG_DIRECTORY = 'LogDirectory'
FILENAME_PREFIX = 'FilenamePrefix'
VERBOSE = 'Verbose'
DIVIDER_CHAR = 'DividerChar'
DIVIDER_NUM = 'DividerNum'
INDENT_CHAR = 'IndentChar'
INDENT_SPACES = 'IndentSpaces'

# define how to load the config file
def load_config_ini():
    """
    Load application configurations from config.ini.
    """
    config = configparser.ConfigParser()
    config_path = os.path.join(MAIN_PATH, '__config.ini')
    
    if not config.read(config_path):
        raise ValueError(f"Failed to read config file at {config_path}")
    
    return config

# load the config file
config = load_config_ini()

# define various constants
ENABLE_LOGGING = config[APP_SETTINGS][ENABLE_LOGGING]
IMG_TYPE = config[APP_SETTINGS][IMAGE_TYPE]
IMG_DIRECTORY = config[APP_SETTINGS][IMG_DIRECTORY]
LOG_DIRECTORY = config[APP_SETTINGS][LOG_DIRECTORY]
FILENAME_PREFIX = config[APP_SETTINGS][FILENAME_PREFIX]
VERBOSE_LEVEL = int(config[APP_SETTINGS][VERBOSE])
DIVIDER_CHAR = config[APP_SETTINGS][DIVIDER_CHAR]
DIVIDER_NUM = int(config[APP_SETTINGS][DIVIDER_NUM])
INDENT_CHAR = config[APP_SETTINGS][INDENT_CHAR]
INDENT_SPACES = int(config[APP_SETTINGS][INDENT_SPACES])
LOG_PATH = os.path.join(MAIN_PATH, LOG_DIRECTORY, f"LOG__{T36}.log")
IMG_path = os.path.join(MAIN_PATH, IMG_DIRECTORY, f"IMG__{T36}.png")


# setup the logging system which prints to terminal and will save a text file later.
def configure_logging():
    log_path = os.path.join(MAIN_PATH, LOG_DIRECTORY, "LOG__" + T36 + ".log")
    logging.basicConfig(filename=log_path, level=logging.NOTSET,
                        format='%(asctime)s - %(message)s')

# run the logging setup
configure_logging()

def dict_frame_info(frame):
    """
    gETs a fRAME oBJECT aND rETURNS a dICTIONARY wITH iTS rELEVANT iNFORMATION.

    :pARAM fRAME: tHE fRAME oBJECT.
    :tYPE fRAME: <fRAME oBJECT>
    :rETURN: dICTIONARY wITH fRAME iNFORMATION.
    :rTYPE: dICT
    """
    return {
        'filename': frame.f_code.co_filename, # fILE nAME wHERE tHE fRAME oRIGINATED.
        'line_no': frame.f_lineno,            # lINE nUMBER iN tHE sOURCE cODE.
        'function': frame.f_code.co_name,     # fUNCTION nAME.
        'global_vars': frame.f_globals,       # gLOBAL vARIABLES aVAILABLE iN tHIS fRAME.
        'local_vars': frame.f_locals          # lOCAL vARIABLES aVAILABLE iN tHIS fRAME.
    }

def log(level, message, emoji=""):            
        
    # Check if ENABLE_LOGGING is False
    if ENABLE_LOGGING == 'False':
        return

    msg_ascii = message

    # handle ints
    if isinstance(msg_ascii, int):
        
        msg_ascii = str(msg_ascii)
    
    if isinstance(msg_ascii, float):
        msg_ascii = str(msg_ascii)
    
    # hANDLE lISTS
    elif isinstance(msg_ascii, list):
        for i, item in enumerate(msg_ascii):
            message = f"[{i}] = {str(item)}"
            emoji = "📜"
            log(level+1, message, emoji)
        return
    
    # handle dictionaries
    elif isinstance(msg_ascii, dict):
        table = PrettyTable()
        table.field_names = ["KEY", "VALUE"]
        
        # Set alignment to the left for both columns
        table.align["KEY"] = "l"
        table.align["VALUE"] = "l"
        
        for k, v in msg_ascii.items():
            # Handle nested dictionaries and lists
            if isinstance(v, dict) or isinstance(v, list):
                nested_table = PrettyTable()
                nested_table.field_names = ["KEY", "VALUE"]  # Change the heading to "Index"
                nested_table.align["KEY"] = "l"
                nested_table.align["VALUE"] = "l"
                nested_table.junction_char = "-"
                nested_table.horizontal_char = "-"
                nested_table.vertical_char = "|"
                if isinstance(v, dict):
                    for nested_k, nested_v in v.items():
                        nested_table.add_row([nested_k, nested_v])
                elif isinstance(v, list):
                    for idx, item in enumerate(v):
                        nested_table.add_row([str(idx), item])
                    nested_table.padding_width = 1
        
                table.add_row([k, nested_table])
            else:
                table.add_row([k, v])
        


        table.junction_char = DIVIDER_CHAR
        table.horizontal_char = DIVIDER_CHAR
        table.padding_width = 3

        table_string = str(table)
        table_lines = table_string.split('\n')
        for line in table_lines:
            emoji = "📗"
            log(level, line, emoji)
        # Customize the table junction characters and horizontal padding
        
        return
    
    msg_utf8 = msg_ascii

    # Shortcut for adding stopwatch to completion flag
    if msg_ascii == "stopwatch":
        msg_ascii = perf_timer() + " sec"
        emoji = "⏱️"

    # Shortcut for adding stopwatch to completion flag
    if msg_ascii == "COMPLETE":
        msg_ascii = "COMPLETED AT " + perf_timer() + " sec"
        emoji = "🏁"

    # Shortcut for adding stopwatch to intermediate success flag
    if msg_ascii == "OK":
        current_frame = inspect.currentframe()
        caller_frame = current_frame.f_back
        caller_function = caller_frame.f_code.co_name
        caller_line = caller_frame.f_lineno
        
        msg_ascii = f"{caller_function} line {caller_line} OK @ {perf_timer()} sec"
        emoji = "🆗"

    if msg_ascii == "ERROR":
        current_frame = inspect.currentframe()
        # gOING "uP" tO tHE cALLER's fRAME
        caller_frame = current_frame.f_back
        caller_name = caller_frame.f_code.co_name
        
        msg_ascii = f"{caller_frame} @ {perf_timer()} sec"
        emoji = "E"

    # Check for emoji
    if emoji:
        msg_utf8 = emoji + "  " + msg_ascii

    # build indentation per line
    indent = (INDENT_CHAR + " " * INDENT_SPACES) * level
    # set max length of indentation for highly verbose states
    if level>32:
        indent = (INDENT_CHAR + " " * INDENT_SPACES) * 32

    # build a divider if the input is "---"
    if msg_ascii == "---" and VERBOSE_LEVEL > 0:
        msg_line = "\n" + DIVIDER_CHAR * DIVIDER_NUM + "\n"
        print(msg_line)
        logging.info(msg_line)
        return

    msg_ascii = indent + msg_ascii
    msg_utf8 = indent + msg_utf8    



    if VERBOSE_LEVEL > 9000:
        current_frame = inspect.currentframe()
        # gOING "uP" tO tHE cALLER's fRAME
        caller_frame = current_frame.f_back
        msg_ascii = f"{caller_frame.f_code}\t{msg_ascii}"
        msg_utf8 = f"{caller_frame.f_code}\t{msg_utf8}"

    if VERBOSE_LEVEL >= level:
        print(msg_utf8)
    
    logging.info(msg_ascii)
    
    
    
def log_memory_info_verbose():
    # gET tHE cURRENT fRAME
    frame_inspect = inspect.currentframe()

    # gET tHE cALLER (pARENT) fRAME
    caller_frame = frame_inspect.f_back
    if caller_frame is None:
        print("No caller frame available.")
        return

    # gET tHE aRGUMENTS aND lOCALS fOR tHE cALLER fRAME
    arg_info = inspect.getargvalues(caller_frame)

    # fORMATTING tHE aRGUMENTS aND lOCALS sO eACH iTEM iS oN a nEW lINE
    formatted_args = ',\n'.join(arg_info.args)
    formatted_locals = str(arg_info.locals).replace(", ", ",\n\t")

    # cREATING tHE fINAL sTRING tO pRINT
    print_lines = f"Arguments: [{formatted_args}]\nLocals: {formatted_locals}"
    log(9001, print_lines)


    

# log(1, f"MAIN_PATH: {MAIN_PATH}")
# log(2, f"LOG_DIRECTORY: {LOG_DIRECTORY}")

#listy = [1,2,3,"asdf",222]

#log(0, listy)