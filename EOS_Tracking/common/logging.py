import threading
from time import time 
from typing import Optional
from io import TextIOWrapper

class Logger:

    """
    Logger for EOS-Tracking Modules
    :param filename: Optional file name for logger to write to (if None is provided, no file will be openneds)
    """

    init_time        : float 
    filename         : Optional[str]            = None
    file             : Optional[TextIOWrapper]  = None
    _instance_lock   : threading.Lock = threading.Lock() 


    def __init__(
        self,
        filename        : Optional[str] = None
    ):
        self.init_time = time()
        self.filename  = filename
        
    def __enter__( self ):
        if self.filename is not None:
            self.file = open(self.filename,"w")
        return self

    def __exit__(
        self,
        exception,
        exception_value,
        traceback
    ):
        if isinstance(self.file,TextIOWrapper):
            self.file.close()
        self.file = None
        

    def write(
        self,
        msg          : str,
        process_name : str = " ",
    ):
        """
        Write log information either to file or to console
        :param msg: Message for logger to write 
        :param process_name: Name of process writing message
        """
        def format_msg( process_name, msg ): return "[@{:.2f}] {} -> {} ".format( time() - self.init_time, process_name, msg )

        with self._instance_lock:
            print( format_msg( process_name, msg ) )
            if isinstance(self.file,TextIOWrapper):
                try:
                    self.file.write( format_msg( process_name, msg ) )
                except Exception as e:
                    print( format_msg( "logging.py", "[ERROR]: Logger raised exception {e}" ) )