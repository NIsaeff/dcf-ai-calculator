"""Callback modules for Dash application."""

from .fcff_callbacks import register_fcff_callbacks
from .wacc_callbacks import register_wacc_callbacks
from .dcf_callbacks import register_dcf_callbacks


def register_callbacks(app):
    """Register all application callbacks.
    
    Args:
        app: Dash application instance
    """
    register_fcff_callbacks(app)
    register_wacc_callbacks(app)
    register_dcf_callbacks(app)
