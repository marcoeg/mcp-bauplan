
import logging
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import os
from typing import Dict, Any
import bauplan
import datetime

env_path = os.path.join(os.getcwd(), ".env")
load_dotenv(env_path)
from mcp_bauplan.mcp_config import config

MCP_SERVER_NAME = "mcp-bauplan"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(MCP_SERVER_NAME)

deps = ["starlette", "python-dotenv", "uvicorn", "httpx", "bauplan"]
mcp = FastMCP(MCP_SERVER_NAME, dependencies=deps)

def create_bauplan_client():
    """
    Creates and validates a connection Bauplan.
    Retrieves connection parameters from config, establishes a connection.
    
    Returns:
        Client: A configured Bauplan client instance
        
    Raises:
        ConnectionError: When connection cannot be established
        ConfigurationError: When configuration is invalid
    """
    logger.info(
        f"Creating Bauplan client connection. "
        f"branch={config.branch}, "
        f"namespace={config.namespace},"
        f"timeout={config.timeout}"
    )
    try:
        # Establish connection to Bauplan
        client = bauplan.Client(
            api_key=config.api_key,
            branch=config.branch, 
            namespace=config.namespace, 
            client_timeout=config.timeout
        )
        logger.info(f"Connected to Bauplan. branch={client.profile.branch} - namespace={client.profile.namespace}")   
        return client
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Failed to connect to Bauplan: {str(e)}", exc_info=True)
        raise ConnectionError(f"Unable to connect to Bauplan: {str(e)}")

def execute_query(query: str):
    # Initialize Bauplan client
    bauplan_client = create_bauplan_client()

    try:
        # Create a response structure optimized for LLM consumption
        response = {
            "status": "success",
            "data": [],
            "metadata": {},
            "error": None
        }
        print(f"Executing query: {query}")
        
        # Execute query and get results as Arrow table
        result = bauplan_client.query(
            query=query,
            ref=config.branch
        )

        # Convert pyarrow.Table to list of dictionaries
        data_rows = [dict(zip(result.column_names, row)) for row in zip(*[result[col] for col in result.column_names])]

        # Add data and metadata to response
        response["data"] = data_rows
        response["metadata"] = {
            "row_count": len(data_rows),
            "column_names": result.column_names,
            "column_types": [col[1] for col in result.column_types],
            "query_time": datetime.datetime.now().isoformat(),
            "query": query,
        }
        logger.info(f"Query returned {len(data_rows)} rows")

    except Exception as err:
        # Consistent error handling with detailed information
        error_message = str(err)
        logger.error(f"Error executing query: {error_message}")
        
        # Update response for error case
        response["status"] = "error"
        response["error"] = error_message
        response["data"] = []  # Ensure empty data on error
        
    return response


"""
- `list_tables`:
   - Lists all the tables in the configured namespace
- `get_schema`:
   - Get the schema of a data tables
- `run_query`:
   - Run a SELECT query on the specified table 
"""