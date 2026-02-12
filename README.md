# Orion MCP Client

A Python client for connecting to the [Orion MCP Server](https://github.com/liqcui/orion-mcp) to perform OpenShift performance regression analysis.

## Overview

The Orion MCP (Model Context Protocol) Client provides a convenient Python interface for interacting with the Orion MCP server, which offers tools for:

- **Performance Regression Detection**: Detect performance regressions in OpenShift versions
- **PR Impact Analysis**: Analyze the performance impact of specific pull requests
- **Metrics Correlation**: Visualize correlations between different performance metrics
- **Nightly Build Analysis**: Check nightly builds for performance issues
- **Networking Performance**: Focused analysis on networking-related performance

## Prerequisites

- Python 3.11+
- Access to a running Orion MCP server
- Environment variable `ES_SERVER` set to your OpenSearch/Elasticsearch URL (on the server)

## Installation

1. Install dependencies:

```bash
pip install -r orion_mcp_client_requirements.txt
```

2. Ensure the Orion MCP server is running:

```bash
# On the server machine
cd /path/to/orion-mcp
export ES_SERVER="https://your-opensearch-url"
python orion_mcp.py
```

The server will start on `http://0.0.0.0:3030` by default.

## Quick Start

### Basic Usage

```python
import asyncio
from orion_mcp_client import OrionMCPClient

async def main():
    # Initialize client (update URL if server is on a different host)
    client = OrionMCPClient("http://localhost:3030")

    # Check for regressions
    result = await client.has_openshift_regressed("4.20", "15")
    print(result)

asyncio.run(main())
```

### Running Examples

The package includes comprehensive examples:

```bash
# Run the example script
python orion_mcp_client_advanced_examples.py
```

## Client API Reference

### OrionMCPClient

Main client class for interacting with the Orion MCP server.

#### Constructor

```python
client = OrionMCPClient(server_url="http://localhost:3030")
```

**Parameters:**
- `server_url` (str): Base URL of the Orion MCP server

#### Methods

##### `get_release_date(version: str) -> str`

Get the release date for a given OpenShift version.

```python
date = await client.get_release_date("4.20")
# Returns: "2025-10-23"
```

##### `get_orion_configs() -> List[str]`

Get the list of available Orion configuration files.

```python
configs = await client.get_orion_configs()
# Returns: ["small-scale-udn-l3.yaml", "trt-external-payload-cluster-density.yaml", ...]
```

##### `get_orion_metrics(config: str) -> Dict`

Get available metrics for a specific configuration.

```python
metrics = await client.get_orion_metrics("small-scale-udn-l3.yaml")
# Returns: {"/orion/examples/small-scale-udn-l3.yaml": ["podReadyLatency_P99", "ovnCPU_avg", ...]}
```

##### `openshift_report_on(versions, lookback, metric, config, options) -> Any`

Generate a performance analysis report.

```python
# Get JSON data
report = await client.openshift_report_on(
    versions="4.19,4.20",
    lookback="15",
    metric="podReadyLatency_P99",
    config="small-scale-udn-l3.yaml",
    options="json"
)

# Get image visualization
image = await client.openshift_report_on(
    versions="4.19,4.20",
    lookback="15",
    metric="podReadyLatency_P99",
    config="small-scale-udn-l3.yaml",
    options="image"
)
```

**Parameters:**
- `versions` (str): Comma-separated list of versions (e.g., "4.19,4.20")
- `lookback` (str): Number of days to look back (default: "15")
- `since` (str, optional): Date to begin lookback
- `metric` (str): Metric to analyze (default: "podReadyLatency_P99")
- `config` (str): Configuration file (default: "small-scale-udn-l3.yaml")
- `options` (str): Output format - "image", "json", "both", or "json:fieldName"

##### `openshift_report_on_pr(version, lookback, organization, repository, pull_request) -> Dict`

Analyze the performance impact of a specific pull request.

```python
pr_analysis = await client.openshift_report_on_pr(
    version="4.20",
    organization="openshift",
    repository="ovn-kubernetes",
    pull_request="2841"
)
```

**Returns:** Dictionary with periodic averages and PR-specific metrics, including percentage changes.

##### `has_openshift_regressed(version, lookback) -> str`

Check if OpenShift has performance regressions.

```python
result = await client.has_openshift_regressed("4.19", "15")
# Returns: String describing regressions or "No changepoints found"
```

##### `has_networking_regressed(version, lookback) -> str`

Check for networking-specific performance regressions.

```python
result = await client.has_networking_regressed("4.19", "15")
```

##### `metrics_correlation(metric1, metric2, config, version, lookback) -> Any`

Analyze correlation between two metrics.

```python
correlation = await client.metrics_correlation(
    metric1="podReadyLatency_P99",
    metric2="ovnCPU_avg",
    config="trt-external-payload-cluster-density.yaml",
    version="4.19"
)
# Returns: Image (base64) showing scatter plot with Pearson correlation
```

##### `has_nightly_regressed(nightly_version, previous_nightly, lookback, configs) -> str`

Detect regressions in specific nightly builds.

```python
result = await client.has_nightly_regressed(
    nightly_version="4.22.0-0.nightly-2026-01-05-203335",
    previous_nightly="4.22.0-0.nightly-2026-01-01-123456",
    lookback="30"
)
```

##### `list_tools() -> List[Dict]`

List all available tools on the server.

```python
tools = await client.list_tools()
for tool in tools:
    print(f"{tool['name']}: {tool['description']}")
```

##### `list_resources() -> List[Dict]`

List all available resources on the server.

```python
resources = await client.list_resources()
```

## Examples

### Example 1: Check for Regressions

```python
async def check_regressions():
    client = OrionMCPClient("http://localhost:3030")

    versions = ["4.18", "4.19", "4.20"]
    for version in versions:
        result = await client.has_openshift_regressed(version, "30")
        print(f"OpenShift {version}: {result}")
```

### Example 2: Analyze PR Performance Impact

```python
async def analyze_pr():
    client = OrionMCPClient("http://localhost:3030")

    pr_analysis = await client.openshift_report_on_pr(
        version="4.20",
        organization="openshift",
        repository="ovn-kubernetes",
        pull_request="2841"
    )

    # Check for significant changes (>10% threshold)
    for summary in pr_analysis["summaries"]:
        config = summary["config"]
        for pull_entry in summary["pull"]:
            for metric_name, metric_data in pull_entry["metrics"].items():
                pct_change = metric_data.get("percentage_change", 0)
                if abs(pct_change) > 10:
                    print(f"⚠️  {config}: {metric_name} changed by {pct_change:.2f}%")
```

### Example 3: Generate Performance Comparison Chart

```python
import base64
from pathlib import Path

async def compare_versions():
    client = OrionMCPClient("http://localhost:3030")

    image_result = await client.openshift_report_on(
        versions="4.18,4.19,4.20",
        metric="podReadyLatency_P99",
        config="small-scale-udn-l3.yaml",
        options="image"
    )

    # Save the image
    if image_result.get("type") == "image":
        image_data = base64.b64decode(image_result["data"])
        Path("performance_chart.jpg").write_bytes(image_data)
        print("Chart saved to performance_chart.jpg")
```

### Example 4: Metrics Correlation Analysis

```python
async def analyze_correlation():
    client = OrionMCPClient("http://localhost:3030")

    result = await client.metrics_correlation(
        metric1="podReadyLatency_P99",
        metric2="ovnCPU_avg",
        config="trt-external-payload-cluster-density.yaml",
        version="4.20"
    )

    # Save correlation plot
    if result.get("type") == "image":
        image_data = base64.b64decode(result["data"])
        Path("correlation.jpg").write_bytes(image_data)
```

## Available Metrics

Common metrics available for analysis (varies by configuration):

- `podReadyLatency_P99` - 99th percentile pod ready latency
- `ovnCPU_avg` - Average OVN CPU usage
- `apiCallLatency_P99` - 99th percentile API call latency
- `clusterDensity` - Cluster density metrics
- And many more...

Use `get_orion_metrics(config)` to see all available metrics for a specific configuration.

## Available Configurations

Common Orion configurations:

- `small-scale-udn-l3.yaml` - Small-scale UDN L3 networking
- `med-scale-udn-l3.yaml` - Medium-scale UDN L3 networking
- `trt-external-payload-cluster-density.yaml` - Cluster density testing
- `trt-external-payload-node-density.yaml` - Node density testing
- `trt-external-payload-node-density-cni.yaml` - CNI-focused node density
- `trt-external-payload-crd-scale.yaml` - CRD scale testing
- `metal-perfscale-cpt-virt-udn-density.yaml` - Metal virtualization density

Use `get_orion_configs()` to see all available configurations on your server.

## Understanding Results

### Regression Detection

The Orion server uses an **EDivisive algorithm** to detect performance changepoints. A changepoint indicates a significant shift in performance metrics.

When regressions are detected, you'll see:
- UUID of the problematic test run
- OpenShift version affected
- PRs that were added since the previous version
- Metrics that changed and by how much

### PR Analysis

For PR analysis, the server compares:
- `periodic_avg`: Average performance from periodic CI runs
- `pull`: Performance from PR-specific test runs

**Use a 10% threshold** to determine significance:
- If a metric changes by >10%, it's considered a regression
- The `percentage_change` field is calculated automatically

### Output Formats

When using `openshift_report_on`:

- `options="json"` - Returns raw data as JSON
- `options="image"` - Returns base64-encoded image
- `options="both"` - Returns both JSON and image data
- `options="json:fieldName"` - Returns JSON grouped by specified field

## Troubleshooting

### Connection Errors

If you get connection errors:

1. Verify the server is running:
   ```bash
   curl http://localhost:3030/health
   ```

2. Check the server URL in your client code

3. Ensure `ES_SERVER` environment variable is set on the server

### No Data Returned

If queries return empty results:

1. Check that the OpenSearch/Elasticsearch instance has data
2. Verify the lookback period is appropriate
3. Confirm the OpenShift version exists in the data

### Import Errors

If you get import errors:

```bash
pip install --upgrade -r orion_mcp_client_requirements.txt
```

## Architecture

The client uses the MCP (Model Context Protocol) with `streamable-http` transport:

```
Client App
    ↓
OrionMCPClient
    ↓
streamablehttp_client (MCP transport)
    ↓
ClientSession (MCP session management)
    ↓
HTTP/SSE Connection
    ↓
Orion MCP Server (FastMCP)
    ↓
Orion Library (Performance Analysis)
    ↓
OpenSearch/Elasticsearch (Data Store)
```

### Session Management

Each tool call creates a new session:
1. Connect via streamable HTTP
2. Initialize MCP session
3. Get session ID
4. Call tool with parameters
5. Return results
6. Session closes automatically

## Contributing

When adding new methods to the client:

1. Match the tool name exactly as defined in `orion_mcp.py`
2. Include proper type hints
3. Add docstrings with parameter descriptions
4. Handle both JSON and image return types appropriately
5. Add examples to the advanced examples file

## License

This client is designed to work with the [Orion MCP Server](https://github.com/liqcui/orion-mcp) and follows the same licensing.

## References

- [Orion MCP Server](https://github.com/liqcui/orion-mcp)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Cloud Bulldozer Orion](https://github.com/cloud-bulldozer/orion)

## Support

For issues related to:
- **The client**: Check this README and examples
- **The server**: See the [Orion MCP repository](https://github.com/liqcui/orion-mcp)
- **The underlying analysis**: Check [Orion documentation](https://github.com/cloud-bulldozer/orion)
