"""
System App Configuration for FCJ Pizza

Purpose:
- Configures the core 'system' application.
- Registers and starts the background system automation engine when Django starts.

Broader System Integration:
- Ensures the background daemon thread runs continuously within the main server process
  to handle stale order cancellations and end-of-day sales compiling.
"""

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class SystemConfig(AppConfig):
    """
    Django app config for the core system module.
    Automatically initializes the background automation engine upon startup.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "sales_inventory_system.system"

    def ready(self):
        """
        Executes when the Django application is fully loaded.
        Spawns and starts the background automation daemon thread.
        """
        try:
            from .automation import start_automation_engine
            start_automation_engine()
        except Exception as e:
            logger.error(f"Failed to start system background automation engine: {e}")

