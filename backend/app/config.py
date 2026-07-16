"""
Central configuration for PhoenixForge AI.
Reads everything from environment variables (loaded from .env by python-dotenv).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() == "true"

    # How to reach real DataHub when DEMO_MODE=false.
    #   "mcp"      -> DataHub MCP Server (mcp-server-datahub). Recommended: this is the
    #                 hackathon's primary agent-integration surface.
    #   "graphql"  -> direct GraphQL calls to DataHub GMS. Kept as a documented fallback
    #                 for environments where running the MCP server isn't possible.
    INTEGRATION_MODE: str = os.getenv("INTEGRATION_MODE", "mcp")

    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    DATAHUB_GMS_URL: str = os.getenv("DATAHUB_GMS_URL", "http://localhost:8080")
    DATAHUB_TOKEN: str = os.getenv("DATAHUB_TOKEN", "")

    # Command used to launch the DataHub MCP Server as a subprocess (stdio transport).
    # Default uses uvx so no separate install step is needed; pin a version in your
    # own .env once you've verified compatibility, e.g. "uvx mcp-server-datahub==0.6.0".
    MCP_SERVER_COMMAND: str = os.getenv("MCP_SERVER_COMMAND", "uvx mcp-server-datahub@latest")
    MCP_ENABLE_MUTATIONS: bool = os.getenv("MCP_ENABLE_MUTATIONS", "true").lower() == "true"

    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_REPO: str = os.getenv("GITHUB_REPO", "")

    PORT: int = int(os.getenv("PORT", "8000"))

    DB_URL: str = os.getenv("DB_URL", "sqlite:///./phoenixforge.db")

    SAMPLE_DATA_PATH: str = os.getenv(
        "SAMPLE_DATA_PATH",
        os.path.join(os.path.dirname(__file__), "..", "..", "sample_data", "mock_datahub_metadata.json"),
    )


settings = Settings()
