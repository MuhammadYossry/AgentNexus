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
    Central system for routing component events to their handlers.
    This class manages the registration of components and their event handlers,
    and provides methods for dispatching events to the appropriate handlers.
    """
    _instance = None
    _initialized = False  # Move this to class level

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ComponentEventDispatcher, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once
        if not ComponentEventDispatcher._initialized:
            self.registered_components = {}
            self.event_handlers = {}
            self.action_handlers = {}
            ComponentEventDispatcher._initialized = True
            logger.debug("Initialized new ComponentEventDispatcher instance")

    def register_component(self, component: UIComponent) -> None:
        """
        Register a component and its handlers with the dispatcher.

        Args:
            component: The UI component to register
        """
        if not hasattr(component, 'component_key'):
            logger.warning(f"Component missing component_key: {component}")
            return
            
        component_key = component.component_key
        
        # Register the component itself
        self.registered_components[component_key] = component
        
        # Register event handlers
        if hasattr(component, 'event_handlers'):
            if component_key not in self.event_handlers:
                self.event_handlers[component_key] = {}
            for event_name, handler in component.event_handlers.items():
                self.event_handlers[component_key][event_name] = handler
                logger.debug(f"Registered event handler for {component_key}.{event_name}")
                # For backward compatibility, also register in action_handlers
                if component_key not in self.action_handlers:
                    self.action_handlers[component_key] = {}
                # Map common event names to action names for compatibility
                action_name = event_name
                if event_name == 'row_click':
                    action_name = 'select_seat'
                elif event_name == 'submit':
                    action_name = 'search_seats'
                self.action_handlers[component_key][action_name] = handler
                logger.debug(f"Also registered as action handler for {component_key}.{action_name}")
    
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
                # For backward compatibility, also register in action_handlers
                if component_key not in self.action_handlers:
                    self.action_handlers[component_key] = {}
                # Map common event names to action names for compatibility
                action_name = event_name
                if event_name == 'row_click':
                    action_name = 'select_seat'
                elif event_name == 'submit':
                    action_name = 'search_seats'
                self.action_handlers[component_key][action_name] = handler
                logger.debug(f"Also registered as action handler for {component_key}.{action_name}")

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
        # Also register as event handler if it maps to a known event
        if component_key not in self.event_handlers:
            self.event_handlers[component_key] = {}
        # Map action names to event names
        event_name = action
        if action == 'select_seat':
            event_name = 'row_click'
        elif action == 'search_seats':
            event_name = 'submit'
        self.event_handlers[component_key][event_name] = handler
        logger.debug(f"Also registered as event handler for {component_key}.{event_name}")

    async def dispatch_event(self, component_key: str, event_name: str,
                           event_data: Dict[str, Any]) -> Union[UIResponse, Dict[str, Any], None]:
        """
        Dispatch an event to the appropriate handler.

        Args:
            component_key: Key of the component that triggered the event
            event_name: Type of event that was triggered
            event_data: Data associated with the event

        Returns:
            The result of the handler

        Raises:
            EventDispatchError: If no handler is found or handling fails
        """
        # Look for the handler
        handler = self.event_handlers.get(component_key, {}).get(event_name)
        if not handler:
            logger.warning(f"No handler found for event {event_name} on component {component_key}")
            raise EventDispatchError(f"No handler found for event {event_name}")

        try:
            # Get handler parameters
            handler_params = inspect.signature(handler).parameters
            # Prepare the data to match the handler's parameters
            handler_args = {
                'action': event_name,
                'data': event_data,  # Pass the entire event_data as 'data'
                'component_key': component_key
            }
            # Add any additional data from event_data that matches parameter names
            for param_name in handler_params.keys():
                if param_name in event_data and param_name not in handler_args:
                    handler_args[param_name] = event_data[param_name]
            # Filter to only include parameters that the handler accepts
            filtered_args = {k: v for k, v in handler_args.items() if k in handler_params}
            logger.debug(f"Calling handler with args: {filtered_args}")
            # Call the handler
            if inspect.iscoroutinefunction(handler):
                result = await handler(**filtered_args)
            else:
                result = handler(**filtered_args)
            return result
        except Exception as e:
            logger.error(f"Error dispatching event {event_name}: {str(e)}", exc_info=True)
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
            The result of the handler

        Raises:
            EventDispatchError: If no handler is found or handling fails
        """
        # Look for the handler
        handler = self.action_handlers.get(component_key, {}).get(action_name)
        if not handler:
            logger.warning(f"No handler found for action {action_name} on component {component_key}")
            raise EventDispatchError(f"No handler found for action {action_name}")
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
            # Call the handler
            if inspect.iscoroutinefunction(handler):
                result = await handler(**filtered_data)
            else:
                result = handler(**filtered_data)
            return result
        except Exception as e:
            logger.error(f"Error dispatching action {action_name}: {str(e)}", exc_info=True)
            raise EventDispatchError(f"Error dispatching action: {str(e)}")

    def register_event_handler(self, component_key: str, event_name: str, handler: Callable) -> None:
        """Register an event handler directly."""
        if component_key not in self.event_handlers:
            self.event_handlers[component_key] = {}
        self.event_handlers[component_key][event_name] = handler
        logger.debug(f"Registered event handler for {component_key}.{event_name}")
        # Map common event names to action names for compatibility
        action_name = event_name
        if event_name == 'row_click':
            action_name = 'select_seat'
        elif event_name == 'submit':
            action_name = 'search_seats'
        # Also register as action handler
        if component_key not in self.action_handlers:
            self.action_handlers[component_key] = {}
        self.action_handlers[component_key][action_name] = handler

# Global dispatcher instance
global_event_dispatcher = ComponentEventDispatcher()