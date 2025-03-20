from rohan.common.base       import _RohanBase, _RohanThreading
from abc                     import abstractmethod
from rohan.common.logging    import Logger
from typing                  import Optional, TypeVar


SelfGuidanceBase = TypeVar("SelfGuidanceBase", bound="GuidanceBase" )
class GuidanceBase(_RohanBase):
    """
    Base class for an arbitrary manipulator guidance
    :param logger: rohan Logger() instance
    """

    process_name    : str = "unnamed guidance"
    logger          : Optional[Logger]

    def __init__( 
        self,
        logger : Optional[Logger] = None  
    ):
        self.logger = logger

    def __enter__( self ):
        self.init_guidance()
        if isinstance(self.logger,Logger): 
            self.logger.write(
                f'Guidance initialized',
                process_name=self.process_name
            )
        return self

    def __exit__( self, exception_type, exception_value, traceback ):
        self.deinit_guidance()        
        if isinstance(self.logger,Logger): 
            self.logger.write(
                f'Guidance cleaned-up',
                process_name=self.process_name
            )

    @abstractmethod
    def init_guidance( self ):
        """
        Initializes guidance
        """

    @abstractmethod
    def deinit_guidance( self ):
        """
        Cleans up artifacts openned by guidance initialization
        """


SelfThreadedGuidanceBase = TypeVar("SelfThreadedGuidanceBase", bound="ThreadedGuidanceBase" )
class ThreadedGuidanceBase(GuidanceBase,_RohanThreading):
    """
    Base class for an arbitrary manipulator guidance spinning up a threaded method
    :param logger: rohan Logger() instance
    """

    process_name : str = "unnamed threaded guidance"
    
    def __init__( 
        self,
        logger : Optional[Logger] = None  
    ):
        GuidanceBase.__init__( self, logger=logger )
        _RohanThreading.__init__( self )
    
    def __enter__( self ):
        GuidanceBase.__enter__( self )
        self.start_spin()
        if isinstance(self.logger,Logger): 
            self.logger.write(
                f'Spinning up guidance thread',
                process_name=self.process_name
            )
        return self
    
    def __exit__( self, exception_type, exception_value, traceback ):
        self.stop_spin()
        if isinstance(self.logger,Logger): 
            self.logger.write(
                f'Unravelling guidance thread',
                process_name=self.process_name
            )
        GuidanceBase.__exit__( self, exception_type, exception_value, traceback )
