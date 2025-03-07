"""
Decorators and factory functions for creating UI components with integrated event handlers.
"""
from typing import Dict, Any, Callable, Optional, List, Type, Union
from functools import wraps
import inspect
import logging
from pydantic import BaseModel

from agents_manifest.ui_components import (
    UIComponent, TableComponent, CodeEditorComponent, FormComponent, 
    MarkdownComponent, ActionHandlerRegistry, TableColumn, FormField,
    ComponentEventType
)

logger = logging.getLogger(__name__)


def component_factory(component_cls: Type[UIComponent], **default_values):
    """
    Factory function for creating UI components with default values.
    
    Args:
        component_cls: The component class to instantiate
        **default_values: Default values for the component
        
    Returns:
        A function that creates a component instance with the provided values
    """
    def create_component(**kwargs):
        # Merge default values with provided kwargs
        config = {**default_values, **kwargs}
        
        # Extract handler functions from kwargs
        handler_functions = {}
        for key, value in list(config.items()):
            if key.startswith('on_') and callable(value):
                event_type = key[3:]  # Remove 'on_' prefix
                handler_functions[event_type] = value
                # Keep the handler in config for proper initialization
        
        # Create component instance
        component = component_cls(**config)
        
        return component
    
    return create_component


def ui_component_decorator(component_cls: Type[UIComponent], **default_values):
    """
    Decorator factory for defining components with inline handlers.
    
    This decorator allows defining a component and its handlers in a single
    function, improving code organization and readability.
    
    Args:
        component_cls: The component class to instantiate
        **default_values: Default values for the component
        
    Returns:
        A decorator that processes the function to extract handlers
    """
    def decorator(component_func):
        """
        Decorator that transforms a function into a component with handlers.
        
        The decorated function should define handlers as methods with names
        starting with 'handle_', which will be extracted and registered.
        
        Args:
            component_func: Function that returns a component definition
            
        Returns:
            A function that creates a fully configured component
        """
        @wraps(component_func)
        def wrapper(**kwargs):
            # Create base component configuration
            config = {**default_values, **kwargs}
            
            # Create a component instance
            component = component_cls(**config)
            
            # Get component instance with any custom setup from the function
            result = component_func(component)
            
            # Use the component from the function if one was returned
            if isinstance(result, UIComponent):
                component = result
            
            # Extract and register methods defined in the function
            for name, member in inspect.getmembers(component_func):
                # Check for handler methods (starting with handle_)
                if name.startswith('handle_') and callable(member):
                    event_type = name[7:]  # Remove 'handle_' prefix
                    
                    # Check if this is an action handler (e.g., handle_action_format)
                    if component.component_type == 'code_editor' and event_type.startswith('action_'):
                        action_name = event_type[7:]  # Remove 'action_' prefix
                        
                        # Ensure we have an action handler registry
                        if not hasattr(component, 'action_handler_registry') or not component.action_handler_registry:
                            component.action_handler_registry = ActionHandlerRegistry()
                        
                        # Register the action handler
                        component.action_handler_registry.register_action_handler(action_name, member)
                        logger.debug(f"Registered action handler {action_name} for {component.component_key}")
                    else:
                        # Register as regular event handler
                        try:
                            if event_type in component.valid_event_types:
                                component.event_handlers[event_type] = member
                                logger.debug(f"Registered event handler {event_type} for {component.component_key}")
                            else:
                                logger.warning(f"Invalid event type {event_type} for {component.component_key}")
                        except ValueError as e:
                            logger.warning(f"Could not register handler {name}: {str(e)}")
            
            return component
        
        return wrapper
    
    return decorator


# Specific decorators for common component types

def table_component(**kwargs):
    """
    Decorator for creating table components with inline handlers.
    
    Args:
        **kwargs: Configuration for the table component
        
    Returns:
        A decorator that processes the function to extract handlers
    """
    return ui_component_decorator(TableComponent, **kwargs)


def code_editor_component(**kwargs):
    """
    Decorator for creating code editor components with inline handlers.
    
    Args:
        **kwargs: Configuration for the code editor component
        
    Returns:
        A decorator that processes the function to extract handlers
    """
    return ui_component_decorator(CodeEditorComponent, **kwargs)


def form_component(**kwargs):
    """
    Decorator for creating form components with inline handlers.
    
    Args:
        **kwargs: Configuration for the form component
        
    Returns:
        A decorator that processes the function to extract handlers
    """
    return ui_component_decorator(FormComponent, **kwargs)


def markdown_component(**kwargs):
    """
    Factory function for creating markdown components.
    
    Args:
        **kwargs: Configuration for the markdown component
        
    Returns:
        A MarkdownComponent instance
    """
    return component_factory(MarkdownComponent, **kwargs)


# Factory functions for creating components programmatically

def create_table_component(**kwargs):
    """
    Create a table component with the provided configuration.
    
    Args:
        **kwargs: Configuration for the table component
        
    Returns:
        A TableComponent instance
    """
    return component_factory(TableComponent, **kwargs)()


def create_code_editor_component(**kwargs):
    """
    Create a code editor component with the provided configuration.
    
    Args:
        **kwargs: Configuration for the code editor component
        
    Returns:
        A CodeEditorComponent instance
    """
    return component_factory(CodeEditorComponent, **kwargs)()


def create_form_component(**kwargs):
    """
    Create a form component with the provided configuration.
    
    Args:
        **kwargs: Configuration for the form component
        
    Returns:
        A FormComponent instance
    """
    return component_factory(FormComponent, **kwargs)()


def create_markdown_component(**kwargs):
    """
    Create a markdown component with the provided configuration.
    
    Args:
        **kwargs: Configuration for the markdown component
        
    Returns:
        A MarkdownComponent instance
    """
    return component_factory(MarkdownComponent, **kwargs)()


# Helper decorator for attaching event handler metadata
def event_handler(event_type: str, component_key: Optional[str] = None):
    """
    Decorator to mark a function as an event handler with metadata.
    
    Args:
        event_type: The type of event this handler will process
        component_key: Optional key to specify which component this handler is for
                      (useful when multiple components of same type exist)
    
    Returns:
        Decorated function with event handler metadata
    """
    def decorator(func):
        """Set event handler metadata on the function."""
        func._event_handler_metadata = {
            "event_type": event_type,
            "component_key": component_key
        }
        return func
    return decorator


# Helper decorator for attaching action handler metadata
def component_action_handler(action_name: str, component_key: Optional[str] = None):
    """
    Decorator to mark a function as an action handler with metadata.
    
    Args:
        action_name: The name of the action this handler will process
        component_key: Optional key to specify which component this handler is for
                      (useful when multiple components of same type exist)
    
    Returns:
        Decorated function with action handler metadata
    """
    def decorator(func):
        """Set action handler metadata on the function."""
        func._action_handler_metadata = {
            "action_name": action_name,
            "component_key": component_key
        }
        return func
    return decorator