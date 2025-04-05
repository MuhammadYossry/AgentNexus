"""
Event dispatching system for UI components with integrated handlers.
"""
from typing import Dict, Any, Callable, Union
import inspect
from loguru import logger

from agentnexus.base_types import UIResponse
from agentnexus.ui_components import UIComponent

class EventDispatchError(Exception):
    """Error raised during event dispatching."""
    pass

class ComponentEventDispatcher:
    """
    Central system for routing component events to their handlers.
    This class manages the registration of components and their event handlers,
    and provides methods for dispatching events to the appropriate handlers.
    """
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ComponentEventDispatcher, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once, Singleton pattern
        if not ComponentEventDispatcher._initialized:
            self.registered_components = {}
            self.event_handlers = {}
            ComponentEventDispatcher._initialized = True
            logger.debug("Initialized new ComponentEventDispatcher instance")

    def register_component(self, component: UIComponent) -> None:
        """Register a component and its handlers with enhanced event support."""
        if not hasattr(component, 'component_key'):
            logger.warning(f"Component missing component_key: {component}")
            return
        component_key = component.component_key
        self.registered_components[component_key] = component
        # Initialize handlers if not exist
        if component_key not in self.event_handlers:
            self.event_handlers[component_key] = {}
        # Register event handlers
        if hasattr(component, 'event_handlers'):
            for event_name, handler in component.event_handlers.items():
                self.event_handlers[component_key][event_name] = handler
                logger.debug(f"Registered event handler for {component_key}.{event_name}")

    def register_component_handlers(self, component: UIComponent) -> None:
        """
        Register only the handlers from a component without storing the component itself.

        Args:
            component: The UI component whose handlers should be registered
        """
        if not hasattr(component, 'component_key'):
            logger.warning(f"Component missing component_key: {component}")
            return
        component_key = component.component_key
        # Register event handlers
        if hasattr(component, 'event_handlers'):
            if component_key not in self.event_handlers:
                self.event_handlers[component_key] = {}
            for event_name, handler in component.event_handlers.items():
                self.event_handlers[component_key][event_name] = handler
                logger.debug(f"Registered event handler for {component_key}.{event_name}")

    async def dispatch_event(self, component_key: str, event_name: str,
                            event_data: Dict[str, Any]) -> Union[UIResponse, Dict[str, Any], None]:
        """Dispatch an event to the appropriate handler with better fallback handling."""
        try:
            logger.debug(f"Dispatching event: {event_name} for component: {component_key}")
            logger.debug(f"Available event handlers: {self.event_handlers.keys()}")
            handler_event_name = event_name
            component_handlers = self.event_handlers.get(component_key, {})
            handler = component_handlers.get(handler_event_name) or component_handlers.get(event_name)

            if not handler:
                # Try fallback handlers
                handler = component_handlers.get('__default__')
                if not handler:
                    # For form components, provide generic submit handler
                    if event_name == 'submit' or event_name == 'process_step':
                        logger.debug(f"Using generic submit handler for {component_key}.{event_name}")
                        return {
                            "action": event_name,
                            "component_key": component_key,
                            "data": event_data.get('data', {}),
                            "values": event_data.get('values', {}),
                            "submitted": True
                        }

                if not handler:
                    logger.warning(f"No handler found for event {event_name} on component {component_key}")
                    raise EventDispatchError(f"No handler found for event {event_name}")

            # Get handler parameters
            handler_params = inspect.signature(handler).parameters
            # Prepare the data to match the handler's parameters
            handler_args = {
                'action': handler_event_name,  # Use the mapped event name
                'data': event_data.get('data', event_data),  # Try to get data field or use entire event_data
                'component_key': component_key,
                'values': event_data.get('values', {})
            }

            # Add any additional fields from event_data
            for key, value in event_data.items():
                if key in handler_params and key not in handler_args:
                    handler_args[key] = value
            # Filter to only include parameters that the handler accepts
            filtered_args = {k: v for k, v in handler_args.items() if k in handler_params}
            logger.debug(f"Calling handler with args: {filtered_args}")
            # Call the handler
            if inspect.iscoroutinefunction(handler):
                result = await handler(**filtered_args)
            else:
                result = handler(**filtered_args)
            logger.debug(f"Handler result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error dispatching event {event_name}: {str(e)}", exc_info=True)
            raise EventDispatchError(f"Error dispatching event: {str(e)}")

    def register_event_handler(self, component_key: str, event_name: str, handler: Callable) -> None:
        """Register an event handler directly."""
        if component_key not in self.event_handlers:
            self.event_handlers[component_key] = {}
        self.event_handlers[component_key][event_name] = handler
        logger.debug(f"Registered event handler for {component_key}.{event_name}")

# Global dispatcher instance
global_event_dispatcher = ComponentEventDispatcher()