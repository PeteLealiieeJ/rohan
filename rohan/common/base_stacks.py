from abc                             import abstractmethod
from rohan.common.base               import _RohanBase,_RohanThreading
from rohan.data.classes              import StackConfiguration
from rohan.common.base_cameras       import CameraBase
from rohan.common.base_controllers   import ControllerBase
from rohan.common.base_networks      import NetworkBase
from rohan.common.logging            import Logger
from typing                          import Optional, List, Dict, Union, Any, TypeVar, Type
from contextlib                      import nullcontext, ExitStack
from rohan.utils.timers              import IntervalTimer

SelfStackBase = TypeVar("SelfStackBase", bound="StackBase" )
class StackBase(_RohanBase): 
    """
    Base class for an arbitrary camera(s) + controller(s) + network(s) stack
    :param config: configuration as rohan StackConfiguration() dataclass
    :param spin_intrvl: Inverse-frequency of spinning loop
    """

    process_name : str = "unnamed stack"
    config       : StackConfiguration
    spin_intrvl  : float 


    def __init__( 
        self, 
        config      : Optional[StackConfiguration] = None,
        spin_intrvl : float = -1
    ):
        self.spin_intrvl = spin_intrvl
        self.configure(config=config)

    def configure(
        self,
        config : Optional[StackConfiguration] = None
    ) -> None:
        """
        Configures the stack
        :param config: configuration as rohan StackConfiguration() dataclass
        """
        if isinstance(config,StackConfiguration):
            self.config = config

    def spin( self ) -> None:
        """
        Spin-up stack
        """
        spin_timer = IntervalTimer(interval=self.spin_intrvl)
        with Logger(self.config.log_filename) as logger, ExitStack() as stack: 
            _networks, _cameras, _controllers = self._enter_subcontexts( stack=stack, logger=logger ) 

            if isinstance(logger,Logger): 
                logger.write(
                    f'Spinning Up Stack',
                    process_name=self.process_name
                )
            try:
                while True:
                    spin_timer.await_interval()
                    self.process( 
                        network=_networks, 
                        camera=_cameras, 
                        controller=_controllers
                    )

            except KeyboardInterrupt:
                if isinstance(logger,Logger): 
                    logger.write(
                        f'Spinning Down Stack',
                        process_name=self.process_name
                    )

    def _enter_subcontexts(
        self,
        stack   : ExitStack,
        logger  : Logger,
    ) -> None:
        """
        Enter stack subcomponent contexts
        """
        
        def _enter_subcontext(
            obj_classes     : Optional[int]     = None,
            obj_configs     : Optional[int]     = None,
            obj_baseclass   : Type[_RohanBase]  = _RohanBase
        ):
            """
            Enter contexts of a specified subcomponent type
            """

            if obj_classes is None:
                context = stack.enter_context( nullcontext() ) 
            elif isinstance(obj_classes,List):
                context = [ 
                    stack.enter_context( obj_class( logger=logger, **obj_config ) if obj_class is not None else stack.enter_context( nullcontext() ) ) 
                    for obj_class, obj_config in zip(obj_classes,obj_configs)
                ]
            elif isinstance(obj_classes,Dict):
                context = {
                    key : stack.enter_context( obj_class( logger=logger, **obj_configs[key] ) if obj_class is not None else stack.enter_context( nullcontext() ) ) 
                    for key, obj_class in obj_classes.items()
                }
            else:
                if not issubclass(obj_classes,obj_baseclass):
                    raise TypeError(f"Object provided is not a subclass of {obj_baseclass}: Provided class is {type(obj_classes)} ")
                context = stack.enter_context( obj_classes( logger=logger,**obj_configs ) )

            return context

        if not isinstance(self.config,StackConfiguration):
            if isinstance(logger,Logger): 
                    logger.write(
                        f'No configuration file was loaded and config is {type(self.config)} ... raising RuntimeError',
                        process_name=self.process_name
                    )
            raise RuntimeError("No configuration file was loaded")

        networks    = _enter_subcontext( 
            obj_classes     = self.config.network_classes,
            obj_configs     = self.config.network_configs,
            obj_baseclass   = NetworkBase
        )
        cameras     = _enter_subcontext( 
            obj_classes     = self.config.camera_classes,
            obj_configs     = self.config.camera_configs,
            obj_baseclass   = CameraBase
        )
        controllers = _enter_subcontext( 
            obj_classes     = self.config.controller_classes,
            obj_configs     = self.config.controller_configs,
            obj_baseclass   = ControllerBase
        )

        return networks, cameras, controllers

    @abstractmethod
    def process(  
        self, 
        network     : Optional[ Union[ NetworkBase, List[NetworkBase], Dict[Any,NetworkBase] ] ]               = None,
        camera      : Optional[ Union[ CameraBase, List[CameraBase], Dict[Any,CameraBase] ] ]                  = None,
        controller  : Optional[ Union[ ControllerBase, List[ControllerBase], Dict[Any,ControllerBase] ] ]      = None,
    ) -> None: 
        """
        Processes incoming data from camera(s) to determine control(s) being sent to hardware via specified network(s)
        :param network: network object for sending control to hardware
        :param camera: camera object used to collect vision data
        :param controller: controller object used to determine control from network information and camera data 
        """


SelfThreadedStackBase = TypeVar("SelfThreadedStackBase", bound="ThreadedStackBase" )
class ThreadedStackBase(StackBase,_RohanThreading): 
    """
    Base class for an arbitrary camera(s) + controller(s) + network(s) stack
    :param config: configuration as rohan StackConfiguration() dataclass
    :param spin_intrvl: Inverse-frequency of spinning loop
    """
    
    _instance      = None

    def __init__( 
        self, 
        config      : Optional[StackConfiguration] = None,
        spin_intrvl : float = -1
    ):
        StackBase.__init__( 
            self,
            config=config, 
            spin_intrvl=spin_intrvl 
        )
        _RohanThreading.__init__( self )
        self.add_threaded_method( target=self.spin )

    def configure(
        self,
        config : Optional[StackConfiguration] = None
    ) -> None:
        """
        Configures the stack
        :param config: configuration as rohan StackConfiguration() dataclass
        """
        if not config is None:
            with self._instance_lock:
                StackBase.configure(self,config=config)


    def spin( self ) -> None:
        """
        Spin-up stack
        """
        spin_timer = IntervalTimer(interval=self.spin_intrvl)
        with Logger(self.config.log_filename) as logger, ExitStack() as stack: 
            _networks, _cameras, _controllers = self._enter_subcontexts( stack=stack, logger=logger ) 

            if isinstance(logger,Logger): 
                logger.write(
                    f'Spinning up stack',
                    process_name=self.process_name
                )
            
            while not self.sigterm.is_set():
                spin_timer.await_interval()
                self.process( 
                    network=_networks, 
                    camera=_cameras, 
                    controller=_controllers
                )

            if isinstance(logger,Logger): 
                    logger.write(
                        f'Spinning down stack',
                        process_name=self.process_name
                    )

    @classmethod
    def get_instance(cls):
        """
        Ensure singleton instance
        """
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """
        Create a new singleton instance
        """
        stop_instance_threads = False
        with cls._instance_lock:
            if isinstance( cls._instance, cls ) and not cls._instance.sigterm.is_set():
                stop_instance_threads = True
                
        if stop_instance_threads : cls._instance.stop_spin()
        with cls._instance_lock:
            cls._instance = cls()
        return cls._instance