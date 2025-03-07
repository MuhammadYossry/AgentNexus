"""
Event dispatching system for UI components with integrated handlers.
"""
from typing import Dict, Any, List, Callable, Optional, Type, Union
import inspect
import asyncio
import logging
from fastapi import HTTPException
from pydantic import BaseModel

from agents_manifest.base_types import UIResponse, UIComponentUpdate
from agents_manifest.ui_components import (
    UIComponent, CodeEditorComponent, TableComponent, FormComponent,
    MarkdownComponent, ComponentEventType
)

logger = logging.getLogger(__name__)


class EventDispatchError(Exception):
    """Error raised during event dispatching."""
    pass


class ComponentEventDispatcher:
    """
    Central system for routing components events/actions to component events(actions) handlers.

    Manages the routing of events to the appropriate component handlers
    based on component key and event type. Provides both direct event
    dispatching and dynamic action dispatching.
    """
    def __init__(self):
        """Initialize the dispatcher with empty registries."""
        # Map of component_key to component instance
        self.registered_components: Dict[str, UIComponent] = {}
        # Map of component_key to event_type to handler
        self.event_handlers: Dict[str, Dict[str, Callable]] = {}
        # Map of component_key to action_name to handler
        self.action_handlers: Dict[str, Dict[str, Callable]] = {}

    def register_component(self, component: UIComponent) -> None:
        """
        Register a component and its handlers with the dispatcher.

        Args:
            component: The UI component to register
        """
        # Ensure component has the needed attributes
        if not hasattr(component, 'component_key'):
            logger.warning(f"Component missing component_key: {component}")
            return
            
        component_key = component.component_key
        
        # Register the component itself
        self.registered_components[component_key] = component
        
        # Register event handlers if present
        if hasattr(component, 'event_handlers'):
            if component_key not in self.event_handlers:
                self.event_handlers[component_key] = {}
                
            for event_type, handler in component.event_handlers.items():
                self.event_handlers[component_key][event_type] = handler
                logger.debug(f"Registered handler for {component_key}.{event_type}")
        
        # Register action handlers if component supports them
        if (isinstance(component, CodeEditorComponent) and 
            hasattr(component, 'action_handler_registry') and 
            component.action_handler_registry):
            
            if component_key not in self.action_handlers:
                self.action_handlers[component_key] = {}
                
            # Register action handlers
            for action_name, handler in component.action_handler_registry.handler_functions.items():
                self.action_handlers[component_key][action_name] = handler
                logger.debug(f"Registered action handler for {component_key}.{action_name}")
                
            # Register default action handler if available
            if component.action_handler_registry.default_handler_function:
                self.action_handlers[component_key]["__default__"] = component.action_handler_registry.default_handler_function
                logger.debug(f"Registered default action handler for {component_key}")
    
    def register_component_handlers(self, component: UIComponent) -> None:
        """
        Register only the handlers from a component without storing the component itself.
        Useful for lightweight registration of just the behavior.

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
                
            for event_type, handler in component.event_handlers.items():
                self.event_handlers[component_key][event_type] = handler
                logger.debug(f"Registered handler for {component_key}.{event_type}")
    
    def register_action_handler(self, component_key: str, action: str, handler: Callable) -> None:
        """
        Register an action handler directly.

        Args:
            component_key: Key of the component
            action: Name of the action
            handler: Handler function
        """
        if component_key not in self.action_handlers:
            self.action_handlers[component_key] = {}
            
        self.action_handlers[component_key][action] = handler
        logger.debug(f"Registered action handler for {component_key}.{action}")
    
    def register_components(self, components: List[UIComponent]) -> None:
        """
        Register multiple components with the dispatcher.
        
        Args:
            components: List of UI components to register
        """
        for component in components:
            if callable(component):  
                # If component is a factory function, call it to get the actual component
                try:
                    actual_component = component()
                    if isinstance(actual_component, UIComponent):
                        self.register_component(actual_component)
                    else:
                        logger.warning(f"Component factory did not return a UIComponent: {component}")
                except Exception as e:
                    logger.error(f"Error instantiating component from factory {component}: {str(e)}")
            elif isinstance(component, UIComponent):
                # Regular component instance
                self.register_component(component)
            else:
                logger.warning(f"Unknown component type: {type(component)}")
    
    def get_component(self, component_key: str) -> Optional[UIComponent]:
        """
        Get a registered component by key.
        
        Args:
            component_key: The key of the component to retrieve
            
        Returns:
            The component if found, None otherwise
        """
        return self.registered_components.get(component_key)
    
    def get_event_handler(self, component_key: str, event_type: str) -> Optional[Callable]:
        """
        Get a registered event handler.
        
        Args:
            component_key: Key of the component
            event_type: Type of event
            
        Returns:
            The handler function if found, None otherwise
        """
        component_handlers = self.event_handlers.get(component_key, {})
        return component_handlers.get(event_type)
    
    def get_action_handler(self, component_key: str, action_name: str) -> Optional[Callable]:
        """
        Get a registered action handler.
        
        Args:
            component_key: Key of the component
            action_name: Name of the action

        Returns:
            The handler function if found, None otherwise
        """
        component_actions = self.action_handlers.get(component_key, {})
        # Try to find specific handler
        handler = component_actions.get(action_name)
        # Fall back to default handler if no specific handler found
        if not handler:
            handler = component_actions.get("__default__")
        return handler

    async def dispatch_event(self, component_key: str, event_type: str, 
                          event_data: Dict[str, Any]) -> Union[UIResponse, Dict[str, Any], None]:
        """
        Dispatch an event to the appropriate handler.
        
        Args:
            component_key: Key of the component that triggered the event
            event_type: Type of event that was triggered
            event_data: Data associated with the event
            
        Returns:
            The result of the handler, which can be a UIResponse, dict, or None
            
        Raises:
            EventDispatchError: If no handler is found or handling fails
        """
        # Look for the handler
        handler = self.get_event_handler(component_key, event_type)
        if not handler:
            logger.warning(f"No handler found for event {event_type} on component {component_key}")
            raise EventDispatchError(f"No handler found for event {event_type} on component {component_key}")
        try:
            # Get handler parameters
            handler_params = inspect.signature(handler).parameters
            # Filter event data to match handler parameters
            filtered_data = {k: v for k, v in event_data.items() if k in handler_params}
            # Add metadata if needed by handler
            if 'component_key' in handler_params and 'component_key' not in filtered_data:
                filtered_data['component_key'] = component_key
            if 'event_type' in handler_params and 'event_type' not in filtered_data:
                filtered_data['event_type'] = event_type
            # Call the handler (handle both async and non-async handlers)
            if inspect.iscoroutinefunction(handler):
                result = await handler(**filtered_data)
            else:
                result = handler(**filtered_data)
            return result
        except Exception as e:
            logger.error(f"Error dispatching event {event_type} to {component_key}: {str(e)}", exc_info=True)
            raise EventDispatchError(f"Error dispatching event: {str(e)}")

    async def dispatch_action(self, component_key: str, action_name: str, 
                           action_data: Dict[str, Any]) -> Union[UIResponse, Dict[str, Any], None]:
        """
        Dispatch an action to the appropriate handler.
        
        Args:
            component_key: Key of the component that triggered the action
            action_name: Name of the action that was triggered
            action_data: Data associated with the action
            
        Returns:
            The result of the handler, which can be a UIResponse, dict, or None
            
        Raises:
            EventDispatchError: If no handler is found or handling fails
        """
        # Look for the handler
        handler = self.get_action_handler(component_key, action_name)

        if not handler:
            logger.warning(f"No handler found for action {action_name} on component {component_key}")
            raise EventDispatchError(f"No handler found for action {action_name} on component {component_key}")

        try:
            # Get handler parameters
            handler_params = inspect.signature(handler).parameters

            # Filter action data to match handler parameters
            filtered_data = {k: v for k, v in action_data.items() if k in handler_params}

            # Add metadata if needed by handler
            if 'component_key' in handler_params and 'component_key' not in filtered_data:
                filtered_data['component_key'] = component_key
            if 'action' in handler_params and 'action' not in filtered_data:
                filtered_data['action'] = action_name

            # Call the handler (handle both async and non-async handlers)
            if inspect.iscoroutinefunction(handler):
                result = await handler(**filtered_data)
            else:
                result = handler(**filtered_data)

            return result
        except Exception as e:
            logger.error(f"Error dispatching action {action_name} to {component_key}: {str(e)}", exc_info=True)
            raise EventDispatchError(f"Error dispatching action: {str(e)}")


# Global dispatcher instance for convenience
global_event_dispatcher = ComponentEventDispatcher()


# # Function to extract handlers from modules for easy registration
# def extract_handlers_from_module(module, dispatcher=global_event_dispatcher):
#     """
#     Extract and register event handlers from a module.

#     Looks for functions with event handler metadata and registers them
#     with the specified dispatcher.

#     Args:
#         module: The module to extract handlers from
#         dispatcher: The dispatcher to register handlers with (default: global_event_dispatcher)
#     """
#     for name, func in inspect.getmembers(module, inspect.isfunction):
#         # Check for event handler metadata
#         if hasattr(func, '_event_handler_metadata'):
#             metadata = func._event_handler_metadata
#             component_key = metadata.get('component_key')
#             event_type = metadata.get('event_type')
#             if component_key and event_type:
#                 # Register with dispatcher
#                 if component_key not in dispatcher.event_handlers:
#                     dispatcher.event_handlers[component_key] = {}
#                 dispatcher.event_handlers[component_key][event_type] = func
#                 logger.debug(f"Registered module handler for {component_key}.{event_type}")

#         # Check for action handler metadata
#         if hasattr(func, '_action_handler_metadata'):
#             metadata = func._action_handler_metadata
#             component_key = metadata.get('component_key')
#             action_name = metadata.get('action_name')
#             if component_key and action_name:
#                 # Register with dispatcher
#                 if component_key not in dispatcher.action_handlers:
#                     dispatcher.action_handlers[component_key] = {}
#                 dispatcher.action_handlers[component_key][action_name] = func
#                 logger.debug(f"Registered module action handler for {component_key}.{action_name}")