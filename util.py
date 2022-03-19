# GLOBAL:
COMMAND_LIST = ['forward','backward','volume up','volume down','up','down','pause','play']
COMMAND_LIST_PDF = ['zoom in','in','zoom out','out','scroll up','scroll down','up','down','continue','next','previous']

def get_time_to_display(duration):

    # https://stackoverflow.com/questions/775049/how-do-i-convert-seconds-to-hours-minutes-and-seconds
    seconds = int(duration / 1000.0)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h == 0:
        total_duration = f"{str(m).zfill(2)}:{str(s).zfill(2)}"
    else:
        total_duration = f"{str(h).zfill(2)}:{str(m).zfill(2)}:{str(s).zfill(2)}"
    return total_duration