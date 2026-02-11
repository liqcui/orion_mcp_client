"""
MCP Client for Orion Performance Analysis Server

This client connects to the orion-mcp server and provides methods to call
all available tools for OpenShift performance regression analysis.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from mcp import ClientSession
from mcp.client.streamablehttp import streamablehttp_client


class OrionMCPClient:
    """Client for interacting with the Orion MCP server."""

    def __init__(self, server_url: str = "http://localhost:3030"):
        """
        Initialize the Orion MCP client.

        Args:
            server_url: Base URL of the Orion MCP server (default: http://localhost:3030)
        """
        self.server_url = server_url
        self.mcp_url = f"{server_url}/mcp"
        self.session_id: Optional[str] = None

    async def _call_tool(self, tool_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            params: Parameters to pass to the tool

        Returns:
            Parsed JSON response from the tool
        """
        async with streamablehttp_client(self.mcp_url) as (
            read_stream,
            write_stream,
            get_session_id,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the connection
                await session.initialize()

                # Get session id once connection established
                self.session_id = get_session_id()
                print(f"Session ID: {self.session_id}")

                # Prepare request data
                request_data = {"params": params or {}}

                print(f"Calling tool {tool_name} with params {request_data}")

                # Call the tool
                result = await session.call_tool(tool_name, request_data)

                # Parse and return the result
                # Handle different content types
                if result.content:
                    content = result.content[0]

                    # Handle text content (JSON)
                    if hasattr(content, 'text'):
                        try:
                            return json.loads(content.text)
                        except json.JSONDecodeError:
                            # Return raw text if not valid JSON
                            return content.text

                    # Handle image content
                    elif hasattr(content, 'data'):
                        return {
                            "type": "image",
                            "data": content.data,
                            "mimeType": getattr(content, 'mimeType', 'image/jpeg')
                        }

                return result

    async def get_release_date(self, version: str = "4.20") -> str:
        """
        Get the release date for a given OpenShift version.

        Args:
            version: OpenShift version (e.g., "4.20")

        Returns:
            Release date string or error message
        """
        return await self._call_tool("get_release_date", {"version": version})

    async def get_orion_configs(self) -> List[str]:
        """
        Get the list of available Orion configuration files.

        Returns:
            List of configuration filenames
        """
        return await self._call_tool("get_orion_configs")

    async def get_orion_metrics(self, config: str = "small-scale-udn-l3.yaml") -> Dict:
        """
        Get the list of metrics available for a specific Orion configuration.

        Args:
            config: Configuration filename (e.g., "small-scale-udn-l3.yaml")

        Returns:
            Dictionary with metrics for the configuration
        """
        return await self._call_tool("get_orion_metrics", {"config": config})

    async def openshift_report_on(
        self,
        versions: str = "4.19",
        lookback: str = "15",
        since: Optional[str] = None,
        metric: str = "podReadyLatency_P99",
        config: str = "small-scale-udn-l3.yaml",
        options: str = "image"
    ) -> Any:
        """
        Generate a performance analysis report for specified OpenShift versions.

        Args:
            versions: Comma-separated list of versions (e.g., "4.19,4.20")
            lookback: Number of days to look back (default: "15")
            since: Optional date to begin lookback
            metric: Metric to analyze (default: "podReadyLatency_P99")
            config: Configuration file to use (default: "small-scale-udn-l3.yaml")
            options: Output format: "image", "json", "both", or "json:ocpVirtVersion"

        Returns:
            Image data (base64) or JSON data depending on options
        """
        params = {
            "versions": versions,
            "lookback": lookback,
            "metric": metric,
            "config": config,
            "options": options
        }
        if since:
            params["since"] = since

        return await self._call_tool("openshift_report_on", params)

    async def openshift_report_on_pr(
        self,
        version: str = "4.20",
        lookback: str = "15",
        organization: str = "openshift",
        repository: str = "ovn-kubernetes",
        pull_request: str = "2841"
    ) -> Dict:
        """
        Analyze performance impact of a specific Pull Request.

        Args:
            version: OpenShift version (default: "4.20")
            lookback: Number of days to look back (default: "15")
            organization: GitHub organization (default: "openshift")
            repository: GitHub repository (default: "ovn-kubernetes")
            pull_request: PR number (default: "2841")

        Returns:
            Dictionary with PR performance analysis
        """
        return await self._call_tool("openshift_report_on_pr", {
            "version": version,
            "lookback": lookback,
            "organization": organization,
            "repository": repository,
            "pull_request": pull_request
        })

    async def has_openshift_regressed(
        self,
        version: str = "4.19",
        lookback: str = "15"
    ) -> str:
        """
        Check if OpenShift has performance regressions.

        Args:
            version: OpenShift version to check (default: "4.19")
            lookback: Number of days to look back (default: "15")

        Returns:
            String describing any regressions found or "No regressions found"
        """
        return await self._call_tool("has_openshift_regressed", {
            "version": version,
            "lookback": lookback
        })

    async def has_networking_regressed(
        self,
        version: str = "4.19",
        lookback: str = "15"
    ) -> str:
        """
        Check if networking-specific performance has regressed.

        Args:
            version: OpenShift version to check (default: "4.19")
            lookback: Number of days to look back (default: "15")

        Returns:
            String describing any regressions found or "No regressions found"
        """
        return await self._call_tool("has_networking_regressed", {
            "version": version,
            "lookback": lookback
        })

    async def metrics_correlation(
        self,
        metric1: str = "podReadyLatency_P99",
        metric2: str = "ovnCPU_avg",
        config: str = "trt-external-payload-cluster-density.yaml",
        since: Optional[str] = None,
        version: str = "4.19",
        lookback: str = "15"
    ) -> Any:
        """
        Calculate and visualize correlation between two metrics.

        Args:
            metric1: First metric to analyze
            metric2: Second metric to analyze
            config: Configuration file to use
            since: Optional date to begin lookback
            version: OpenShift version (default: "4.19")
            lookback: Number of days to look back (default: "15")

        Returns:
            Image data (base64) showing scatter plot with correlation
        """
        params = {
            "metric1": metric1,
            "metric2": metric2,
            "config": config,
            "version": version,
            "lookback": lookback
        }
        if since:
            params["since"] = since

        return await self._call_tool("metrics_correlation", params)

    async def has_nightly_regressed(
        self,
        nightly_version: str,
        previous_nightly: str = "",
        lookback: str = "30",
        configs: str = ""
    ) -> str:
        """
        Detect regressions for a specific OpenShift nightly version.

        Args:
            nightly_version: Full nightly version string (e.g., "4.22.0-0.nightly-2026-01-05-203335")
            previous_nightly: Optional previous nightly to compare against
            lookback: Number of days to look back (default: "30")
            configs: Comma-separated list of config files (optional)

        Returns:
            String with regression details or "No regressions found"
        """
        return await self._call_tool("has_nightly_regressed", {
            "nightly_version": nightly_version,
            "previous_nightly": previous_nightly,
            "lookback": lookback,
            "configs": configs
        })

    async def list_tools(self) -> List[Dict]:
        """
        List all available tools on the server.

        Returns:
            List of tool definitions
        """
        async with streamablehttp_client(self.mcp_url) as (
            read_stream,
            write_stream,
            get_session_id,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                self.session_id = get_session_id()

                tools = await session.list_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    }
                    for tool in tools.tools
                ]

    async def list_resources(self) -> List[Dict]:
        """
        List all available resources on the server.

        Returns:
            List of resource definitions
        """
        async with streamablehttp_client(self.mcp_url) as (
            read_stream,
            write_stream,
            get_session_id,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                self.session_id = get_session_id()

                resources = await session.list_resources()
                return [
                    {
                        "uri": resource.uri,
                        "name": resource.name,
                        "description": resource.description
                    }
                    for resource in resources.resources
                ]


# Example usage
async def main():
    """Example usage of the Orion MCP Client."""

    # Initialize client
    client = OrionMCPClient("http://localhost:3030")

    print("=== Orion MCP Client Example ===\n")

    # Example 1: List available tools
    print("1. Listing available tools...")
    tools = await client.list_tools()
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description']}")
    print()

    # Example 2: Get release date
    print("2. Getting release date for OCP 4.20...")
    release_date = await client.get_release_date("4.20")
    print(f"   Release date: {release_date}\n")

    # Example 3: Get available configs
    print("3. Getting available Orion configs...")
    configs = await client.get_orion_configs()
    print(f"   Configs: {configs}\n")

    # Example 4: Get metrics for a config
    print("4. Getting metrics for small-scale-udn-l3.yaml...")
    metrics = await client.get_orion_metrics("small-scale-udn-l3.yaml")
    print(f"   Metrics: {json.dumps(metrics, indent=2)}\n")

    # Example 5: Check for regressions
    print("5. Checking for OpenShift regressions in version 4.19...")
    regressions = await client.has_openshift_regressed("4.19", "15")
    print(f"   Result: {regressions}\n")

    # Example 6: Generate performance report (JSON output)
    print("6. Generating performance report for 4.19,4.20...")
    report = await client.openshift_report_on(
        versions="4.19,4.20",
        lookback="15",
        metric="podReadyLatency_P99",
        config="small-scale-udn-l3.yaml",
        options="json"
    )
    print(f"   Report preview: {str(report)[:200]}...\n")


if __name__ == "__main__":
    asyncio.run(main())
