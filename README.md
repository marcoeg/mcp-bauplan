# mcp-bauplan
A mimimalist Model Context Protocol MCP server to interact with data tables and running Bauplan queries.

Bauplan manages a data store of Iceberg tables in S3.

## Features
- Get Bauplan data tables and their schemas in the configured namespace
- Query Bauplan data tables using SQL (SELECT only)

>It supports both SSE and STDIO transports. 

## Tools
The server implements the following tools to interact with Bauplan data tables:
- `list_tables`:
   - Lists all the tables in the configured namespace
- `get_schema`:
   - Get the schema of a data tables
- `run_query`:
   - Run a SELECT query on the specified table 

## Configuration

1. Create _or edit the Claude Desktop configuration file located at:
   - On macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

2. Add the following:

```json
{
  "mcpServers": {
    "mcp-nvd": {
      "command": "/path/to/uvx",
      "args": ["mcp-bauplan"],
      "env": {
        "BAUPLAN_API_KEY": "your-api-key",
        "BAUPLAN_BRANCH": "your-branch",
        "BAUPLAN_NAMESPACE": "your-namespace",
        // Optional
        "BAUPLAN_TIMEOUT": "query-timeout-secs" // default 30 seconds
      }
    }
  }
}
```

3. Replace `/path/to/uvx` with the absolute path to the `uvx` executable. Find the path with `which uvx` command in a terminal. This ensures that the correct version of `uvx` is used when starting the server.

4. Restart Claude Desktop to apply the changes.

## Development

### Setup

1. **Prerequisites**:
   - Python 3.10 or higher.
   - A Bauplan API key ([request here](https://www.bauplanlabs.com/#join)).
   - `uv` package manager ([installation](https://docs.astral.sh/uv/)).

2. **Clone the Repository**:
```bash
git clone https://github.com/marcoeg/mcp-bauplan
cd mcp-nvd
```

3. **Set Environment Variables**:
   - Create a `.env` file in the project root:
     ```
     BAUPLAN_API_KEY=your-api-key
     BAUPLAN_BRANCH=your-branch
     BAUPLAN_NAMESPACE=your-namespace
     ```

4. **Install Dependencies**:
```bash
uv sync
uv pip install -e .
```

### Run with the MCP Inspector
```bash
cd /path/to/the/repo
source .env

CLIENT_PORT=8077 SERVER_PORT=8078  npx @modelcontextprotocol/inspector uv \
    --directory /path/to/repo/mcp-bauplan run mcp-bauplan
 ```
>Omit `CLIENT_PORT=8077 SERVER_PORT=8078` if standard ports are not conflicting.

Then open the browser to the URL indicated by the MCP Inspector, typically `http://localhost:8077?proxyPort=8078`

> Switch freely between `stdio` and `sse` transport types in the inspector. To use `sse` you need to run the server as explained below.

### Testing with the SSE transport 

#### Run the Server:
```bash
cd /path/to/the/repo
source .env

uv run mcp-bauplan --transport sse --port 9090
```
- Runs with SSE transport on port `9090` by default.

Then open the browser to the URL indicated by the MCP Inspector. Select SSE Transport Type.