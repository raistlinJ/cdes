import multiprocessing
from Trigger.timer_trigger import TimerTrigger
from Swapper.swapper import Swapper
from Monitor.monitor import Monitor
from COREIfx.session_reader import SessionReader
import logging
import time
import sys
import os

def get_sorted_in_dirs(path, dircontains=""):
    logging.debug('get_sorted_in_dirs(): Instantiated')
    name_list = os.listdir(path)
    dirs = []
    for name in name_list:
        fullpath = os.path.join(path,name)
        if os.path.isdir(fullpath) and (dircontains in name):
            dirs.append(fullpath)
    logging.debug('get_sorted_in_dirs(): Completed')
    if dirs != None:
        return sorted(dirs)
    return []

if __name__ == '__main__':
   
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Controller(): instantiated")

    if len(sys.argv) == 2:
        dirs = get_sorted_in_dirs("/tmp/", dircontains="pycore")
        if len(dirs) == 0:
            logging.error("No sessions exist, make sure core-daemon is running. \n You can start it by running /etc/init.d/core-daemon start")
            exit()
        mydir = dirs[0]
        session_number = mydir.split("pycore.")[1]
        logging.warning("Session Number was not passed in; will use latest: " + session_number)

    elif len(sys.argv) == 3:
        session_number = sys.argv[2]
        mydir = os.path.join("/tmp","pycore."+str(sys.argv[2]))
        if os.path.exists(mydir) == False:
            logging.error("Session "+str(sys.argv[2])+" does not exist, make sure core-daemon is running. \n You can start it by running /etc/init.d/core-daemon start")
            exit()

    else:
        logging.error("Usage: python controller.py <monitor_process_path> [session-number]")
        exit()

    cmd = os.path.abspath(sys.argv[1])
    
    sr = SessionReader(session_number)
    conditional_conns = sr.relevant_session_to_JSON()

    omonitor_queue = multiprocessing.Queue()
    
    otrigger_queue = multiprocessing.Queue()

    oswapper_queue = multiprocessing.Queue()

    m = Monitor("monitor", omonitor_queue, cmd)
    mp = multiprocessing.Process(target=m.run_monitor)
    mp.start()

    tp = TimerTrigger("trigger", omonitor_queue, otrigger_queue, conditional_conns)
    tp = multiprocessing.Process(target=tp.process_data)
    tp.start()
    
    sw = Swapper("swapper", otrigger_queue, oswapper_queue, conditional_conns, session_number)
    sw = multiprocessing.Process(target=sw.update_connection)
    sw.start()
    
    # Get output and print to screen
    while True:
        #logging.debug("Processing...)
        time.sleep(0.1)
    
    logging.debug("Controller(): Completed")