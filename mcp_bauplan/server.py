
import logging
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context
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
            ref=config.branch,
            namespace=config.namespace,
            client_timeout=config.timeout
        )

        # Convert pyarrow.Table to list of dictionaries with native Python values
        data_rows = [
            dict(zip(result.column_names, [val.as_py() for val in row]))
            for row in zip(*[result[col] for col in result.column_names])
        ]

        # Add data and metadata to response
        response["data"] = data_rows
        response["metadata"] = {
            "row_count": len(data_rows),
            "column_names": result.column_names,
            "column_types": [str(field.type) for field in result.schema],
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

@mcp.tool(name="list_tables", description="List all data tables in the Bauplan data store.")
def list_tables():
    """
    List all data tables n the configured Bauplan branch and namespace.
    
    Returns:
        dict: Tables object with names
    """
    logger.info(f"Executing list_tables")
    try:
        client =  create_bauplan_client()
        ret = client.get_tables(ref=config.branch, namespace=config.namespace)
        tables = {"tables": [{"name": table.name} for table in ret]}
        return tables
    
    except Exception as err:
        # Consistent error handling with detailed information
        error_message = str(err)
        logger.error(f"Error executing get_schema: {error_message}")
        response = {
            "status": "error",
            "error":  error_message
        }
        return response
    
@mcp.tool(name="get_schema", description="Get the schema of the Bauplan data store.")
def get_schema():
    """
    Return the schema of all data tables in the configured Bauplan branch and namespace.
    
    Returns:
        dict: Schema object with table fields
    """
    logger.info(f"Executing get_schema")
    try:
        client =  create_bauplan_client()
        # Get the tables list
        ret = client.get_tables(ref=config.branch, namespace=config.namespace)
        tables = {"tables": [{"name": table.name} for table in ret]}
        # Iterate to get schemas and build final structure
        schema_data = {
            "schema": [
                {
                    "table": {
                        "name": t["name"],
                        "fields": client.get_table(
                            table=f"{config.namespace}.{t['name']}",
                            ref=config.branch,
                            include_raw=True
                        ).raw['schemas'][0]['fields']
                    }
                }
                for t in tables["tables"]
            ]
        }
        return schema_data
    
    except Exception as err:
        # Consistent error handling with detailed information
        error_message = str(err)
        logger.error(f"Error executing get_schema: {error_message}")
        response = {
            "status": "error",
            "error":  error_message
        }
        return response

@mcp.tool(name="run_query", description="Query the Bauplan data store using SQL.")
def run_query(query: str):
    """
    Executes a query against the Bauplan data store with timeout protection.
    
    Args:
        query (str): SQL query to execute
        
    Returns:
        dict: Response object with status, data, and error information
    """
    # Log query for debugging and audit purposes
    logger.info(f"Executing query: {query}")
    
    # Enforce SELECT query for security (prevent other operations)
    if not query.strip().upper().startswith("SELECT"):
        logger.info(f"Exiting: only SELECT queries are permitted")
        return {
            "status": "error",
            "error": "Only SELECT queries are permitted",
            "data": [],
            "metadata": {"query": query}
        }
    
    result = execute_query(query)
   
    return result
