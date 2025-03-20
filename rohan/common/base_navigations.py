from rohan.common.base       import _RohanBase, _RohanThreading
from abc                     import abstractmethod
from rohan.common.logging    import Logger
from typing                  import Optional, TypeVar


SelfNavigationBase = TypeVar("SelfNavigationBase", bound="NavigationBase" )
class NavigationBase(_RohanBase):
    """
    Base class for an arbitrary manipulator navigation
    :param logger: rohan Logger() instance
    """

    process_name    : str = "unnamed navigation"
    logger          : Optional[Logger]

    def __init__( 
        self,
        logger : Optional[Logger] = None  
    ):
        self.logger = logger

    def __enter__( self ):
        self.init_navigation()
        if isinstance(self.logger,Logger): 
            self.logger.write(
                f'Navigation initialized',
                process_name=self.process_name
            )
        return self

    def __exit__( self, exception_type, exception_value, traceback ):
        self.deinit_navigation()        
        if isinstance(self.logger,Logger): 
            self.logger.write(
                f'Navigation cleaned-up',
                process_name=self.process_name
            )

    @abstractmethod
    def init_navigation( self ):
        """
        Initializes navigation
        """

    @abstractmethod
    def deinit_navigation( self ):
        """
        Cleans up artifacts openned by navigation initialization
        """


SelfThreadedNavigationBase = TypeVar("SelfThreadedNavigationBase", bound="ThreadedNavigationBase" )
class ThreadedNavigationBase(NavigationBase,_RohanThreading):
    """
    Base class for an arbitrary manipulator navigation spinning up a threaded method
    :param logger: rohan Logger() instance
    """

    process_name : str = "unnamed threaded navigation"
    
    def __init__( 
        self,
        logger : Optional[Logger] = None  
    ):
        NavigationBase.__init__( self, logger=logger )
        _RohanThreading.__init__( self )
    
    def __enter__( self ):
        NavigationBase.__enter__( self )
        self.start_spin()
        if isinstance(self.logger,Logger): 
            self.logger.write(
                f'Spinning up navigation thread',
                process_name=self.process_name
            )
        return self
    
    def __exit__( self, exception_type, exception_value, traceback ):
        self.stop_spin()
        if isinstance(self.logger,Logger): 
            self.logger.write(
                f'Unravelling navigation thread',
                process_name=self.process_name
            )
        NavigationBase.__exit__( self, exception_type, exception_value, traceback )
