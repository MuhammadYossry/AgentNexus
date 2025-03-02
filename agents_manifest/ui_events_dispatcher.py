# ui_events_dispatcher.py - Fixed version
from typing import Dict, Any, Callable, Optional, List, Type, Union
from pydantic import BaseModel
import inspect
import logging
from fastapi import HTTPException

from agents_manifest.base_types import UIResponse, UIComponentUpdate
from agents_manifest.ui_components import UIComponentBase

logger = logging.getLogger(__name__)

class EventDispatchError(Exception):
    """Error raised during event dispatching."""
    pass

class ComponentEventDispatcher:
    """
    Central system for registering and dispatching events to UI components.
    """
    def __init__(self):
        # Structure: {component_key: {event_type: handler_function}}
        self._handlers: Dict[str, Dict[str, Callable]] = {}
        # For action-based handlers: {component_key: {action_name: handler_function}}
        self._action_handlers: Dict[str, Dict[str, Callable]] = {}
        logger.debug("Initialized ComponentEventDispatcher")

    def register_component_handlers(self, component: UIComponentBase) -> None:
        """
        Register all handlers from a component based on its attributes.
        """
        component_key = component.key
        logger.debug(f"Registering handlers for component: {component_key}")
        # Register regular event handlers
        if component_key not in self._handlers:
            self._handlers[component_key] = {}
        # Collect handlers from the component's event_handlers
        if hasattr(component, 'event_handlers'):
            for event_type, handler in component.event_handlers.items():
                self._handlers[component_key][event_type] = handler
                logger.debug(f"Registered handler for {component_key}.{event_type}")
        # Register action handlers for components with actions
        if hasattr(component, 'action_handlers') and component.action_handlers:
            if component_key not in self._action_handlers:
                self._action_handlers[component_key] = {}
            # Register each action handler
            for action, handler in component.action_handlers.handlers.items():
                self._action_handlers[component_key][action] = handler
                logger.debug(f"Registered action handler for {component_key}.{action}")
            # Register default action handler if provided
            if component.action_handlers.default_handler:
                self._action_handlers[component_key]['__default__'] = component.action_handlers.default_handler
                logger.debug(f"Registered default action handler for {component_key}")

    def register_handler(self, component_key: str, event_type: str, handler: Callable) -> None:
        """
        Register a single handler for a specific component and event type.
        """
        if component_key not in self._handlers:
            self._handlers[component_key] = {}
        self._handlers[component_key][event_type] = handler
        logger.debug(f"Registered handler for {component_key}.{event_type}")

    def register_action_handler(self, component_key: str, action: str, handler: Callable) -> None:
        """
        Register a handler for a specific action of a component.
        """
        if component_key not in self._action_handlers:
            self._action_handlers[component_key] = {}
        self._action_handlers[component_key][action] = handler
        logger.debug(f"Registered action handler for {component_key}.{action}")
        # Debug: Print all registered action handlers
        logger.debug(f"Currently registered action handlers: {self._action_handlers}")

    async def dispatch_event(self, component_key: str, event_type: str,
                           data: Dict[str, Any]) -> Optional[UIResponse]:
        """
        Dispatch an event to the appropriate handler based on component key and event type.
        """
        # Look for specific event handler
        component_handlers = self._handlers.get(component_key, {})
        handler = component_handlers.get(event_type)
        if not handler:
            logger.warning(f"No handler found for {component_key}.{event_type}.")
            raise EventDispatchError(f"No handler found for event {event_type} on component {component_key}.")

        try:
            # Call the handler with the data
            handler_params = inspect.signature(handler).parameters
            # Filter the data to match handler parameters
            filtered_data = {k: v for k, v in data.items() if k in handler_params}
            # Add event metadata
            if 'component_key' in handler_params and 'component_key' not in filtered_data:
                filtered_data['component_key'] = component_key
            if 'event_type' in handler_params and 'event_type' not in filtered_data:
                filtered_data['event_type'] = event_type
            # Call the handler
            result = await handler(**filtered_data)
            return result
        except Exception as e:
            logger.error(f"Error dispatching event {event_type} to {component_key}: {str(e)}", exc_info=True)
            raise EventDispatchError(f"Error dispatching event: {str(e)}")

    async def dispatch_action(self, component_key: str, action: str,
                            data: Dict[str, Any]) -> Optional[UIResponse]:
        """
        Dispatch an action to the appropriate handler based on component key and action name.
        """
        logger.debug(f"Dispatching action: {action} for component: {component_key}")
        logger.debug(f"Action data: {data}")
        logger.debug(f"All registered action handlers: {self._action_handlers}")
        component_actions = self._action_handlers.get(component_key, {})
        logger.debug(f"Available action handlers for {component_key}: {component_actions}")
        # Try to get the specific handler for this action
        handler = component_actions.get(action)
        # If no specific handler, try default for this component
        if not handler:
            handler = component_actions.get('__default__')
            logger.debug(f"Using default handler: {handler}")
        # If still no handler, raise an error
        if not handler:
            logger.warning(f"No handler found for action {action} on component {component_key}")
            raise EventDispatchError(f"No handler found for action {action} on component {component_key}")
        try:
            # Call the handler with the data
            handler_params = inspect.signature(handler).parameters
            logger.debug(f"Handler parameters: {handler_params}")
            # Filter the data to match handler parameters
            filtered_data = {k: v for k, v in data.items() if k in handler_params}
            logger.debug(f"Filtered data: {filtered_data}")
            # Add action metadata if needed by handler
            if 'component_key' in handler_params and 'component_key' not in filtered_data:
                filtered_data['component_key'] = component_key
            if 'action' in handler_params and 'action' not in filtered_data:
                filtered_data['action'] = action
            # Call the handler
            logger.debug(f"Calling handler with filtered data: {filtered_data}")
            result = await handler(**filtered_data)
            logger.debug(f"Handler result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error dispatching action {action} to {component_key}: {str(e)}", exc_info=True)
            raise EventDispatchError(f"Error dispatching action: {str(e)}")


# Create a global dispatcher instance
global_dispatcher = ComponentEventDispatcher()