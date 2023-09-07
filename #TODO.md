# APP_RESORAMA.py

Objectives
- Write array to shared memory for viewing in TouchDesigner
- Add output mode for tiled layout


# FCN_log.py

Objectives
- Create a better visual structure using emojis and columns for the indentation spacing
- Handle recursive lists and dictionaries better
- Move arguments for `log(message, level, emoji)` with default level set to 1 and default emoji ""
- Add functionality for saving dictionaries to JSON files which is toggled in config file
    - if a `message` is of type `dict`, convert that `dict` into `json` and save overwrite a file at `MAIN_PATH/DAT/json/{dict_name}.json`
