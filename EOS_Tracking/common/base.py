import threading
from abc import ABC, abstractmethod
from typing import Optional

class _EOSBase(ABC):
    """
    Base Class for EOS-Tracking Modules
    """
    def load(
        self,
        **kwargs,
    ):
        for key, value in kwargs.items():
            setattr( self, key, value )

class _EOSThreading(ABC):
    """
    Class for spinning off threads in EOS-Tracking modules
    """

    stop_sig        : threading.Event
    spun_thread     : Optional[threading.Thread]
    _process_lock   : threading.Lock = threading.Lock() 


    def __init__( self ):
        self.spun_thread = None
        self.stop_sig    = threading.Event()

    def start_spin( self ) -> None:
        """
        Signal to start threaded process
        """
        def _spin_thread():
            self.stop_sig.clear()
            self.spun_thread = threading.Thread(
                target=self.spin,
            )
            self.spun_thread.start()

        if self.spun_thread is None:
            _spin_thread()
        elif isinstance(self.spun_thread,threading.Thread):
            if not self.spun_thread.is_alive():
                _spin_thread()


    def stop_spin( self ) -> None:
        """
        Signal to stop threaded process
        """            
        self.stop_sig.set()
        if isinstance(self.spun_thread,threading.Thread):
            if self.spun_thread.is_alive():
                self.spun_thread.join()         

    @abstractmethod
    def spin( self ) -> None:
        """
        Threaded process
        """