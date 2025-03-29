"""Environment configuration for the MCP ClntopngickHouse server.

This module handles all environment variable configuration with sensible defaults
and type conversion.
"""

from dataclasses import dataclass
import os

@dataclass
class BauplanConfig:
    """Configuration for Bauplan connection settings.

    This class handles all environment variable configuration related to
    the Bauplan connection. 

    Required environment variables:
        "BAUPLAN_API_KEY": The user Bauplan api key
        "BAUPLAN_BRANCH": The selected branch to use
        "BAUPLAN_NAMESPACE": The namespace inside the branch

         Optional environment variables:
        "BAUPLAN_TIMEOUT": Query timeout in seconds. Default 30 seconds.
    """

    def __init__(self):
        """Initialize the configuration from environment variables."""
        self._validate_required_vars()

    @property
    def api_key(self) -> str:
        """Get the Bauplan api key"""
        return os.environ["BAUPLAN_API_KEY"]

    @property
    def branch(self) -> int:
        """Get the Bauplan branch."""
        return os.environ["BAUPLAN_BRANCH"]

    @property
    def namespace(self) -> int:
        """Get the Bauplan namespace."""
        return os.environ["BAUPLAN_NAMESPACE"]

    @property
    def timeout(self) -> int:
        """Get the connection timeout in seconds.

        Default: 30 seconds.
        """
        return int(os.getenv("BAUPLAN_TIMEOUT", "30"))

    def get_client_config(self) -> dict:
        """Get the configuration dictionary for clickhouse_connect client.

        Returns:
            dict: Configuration ready to be passed to clickhouse_connect.get_client()
        """
        config = {
            "api_key": self.api_key,
            "branch": self.branch,
            "namespace": self.namespace,
            "timeout": self.timeout,
        }

        return config

    def _validate_required_vars(self) -> None:
        """Validate that all required environment variables are set.

        Raises:
            ValueError: If any required environment variable is missing.
        """
        missing_vars = []
        for var in ["BAUPLAN_API_KEY", "BAUPLAN_BRANCH", "BAUPLAN_NAMESPACE"]:
            if var not in os.environ:
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

# Global instance for easy access
config = BauplanConfig()
