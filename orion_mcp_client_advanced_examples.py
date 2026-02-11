"""
Advanced Examples for Orion MCP Client

This module demonstrates various use cases for the Orion MCP client,
including performance analysis, regression detection, and PR analysis.
"""

import asyncio
import base64
import json
from pathlib import Path
from orion_mcp_client import OrionMCPClient


async def example_regression_scan():
    """Example: Comprehensive regression scan across OpenShift versions."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Comprehensive Regression Scan")
    print("="*60 + "\n")

    client = OrionMCPClient("http://localhost:3030")

    versions = ["4.18", "4.19", "4.20"]

    for version in versions:
        print(f"\nScanning OpenShift {version} for regressions...")
        result = await client.has_openshift_regressed(version=version, lookback="30")
        print(f"Result:\n{result}\n")
        print("-" * 60)


async def example_pr_analysis():
    """Example: Analyze performance impact of a pull request."""
    print("\n" + "="*60)
    print("EXAMPLE 2: PR Performance Impact Analysis")
    print("="*60 + "\n")

    client = OrionMCPClient("http://localhost:3030")

    # Analyze a specific PR
    pr_analysis = await client.openshift_report_on_pr(
        version="4.20",
        lookback="15",
        organization="openshift",
        repository="ovn-kubernetes",
        pull_request="2841"
    )

    print("PR Analysis Results:")
    print(json.dumps(pr_analysis, indent=2))

    # Check for regressions (>10% threshold as mentioned in the code)
    if "summaries" in pr_analysis:
        for summary in pr_analysis["summaries"]:
            config = summary.get("config", "unknown")
            print(f"\n--- Config: {config} ---")

            periodic_avg = summary.get("periodic_avg", {})
            pull_data = summary.get("pull", [])

            for pull_entry in pull_data:
                metrics = pull_entry.get("metrics", {})
                has_regression = False

                for metric_name, metric_data in metrics.items():
                    pct_change = metric_data.get("percentage_change", 0)
                    if abs(pct_change) > 10:  # 10% threshold
                        has_regression = True
                        direction = "increased" if pct_change > 0 else "decreased"
                        print(f"  ⚠️  {metric_name} {direction} by {abs(pct_change):.2f}%")

                if not has_regression:
                    print(f"  ✓ No significant regressions detected (within 10% threshold)")


async def example_multi_version_comparison():
    """Example: Compare performance trends across multiple versions."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Multi-Version Performance Comparison")
    print("="*60 + "\n")

    client = OrionMCPClient("http://localhost:3030")

    # Get performance data for multiple versions
    versions = "4.18,4.19,4.20"
    metric = "podReadyLatency_P99"
    config = "small-scale-udn-l3.yaml"

    print(f"Analyzing {metric} across versions {versions}")
    print(f"Configuration: {config}\n")

    # Get JSON data
    report = await client.openshift_report_on(
        versions=versions,
        lookback="30",
        metric=metric,
        config=config,
        options="json"
    )

    if isinstance(report, dict) and "data" in report:
        print("Performance Summary:")
        for version, data in report["data"].items():
            if metric in data:
                values = data[metric].get("value", [])
                if values:
                    avg_value = sum(v for v in values if v is not None) / len([v for v in values if v is not None])
                    print(f"  {version}: Average = {avg_value:.2f}ms")

    # Also get image visualization
    print("\nGenerating visualization...")
    image_result = await client.openshift_report_on(
        versions=versions,
        lookback="30",
        metric=metric,
        config=config,
        options="image"
    )

    if isinstance(image_result, dict) and image_result.get("type") == "image":
        # Save the image
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"performance_comparison_{metric}.jpg"

        image_data = base64.b64decode(image_result["data"])
        output_path.write_bytes(image_data)
        print(f"Image saved to: {output_path}")


async def example_metrics_correlation():
    """Example: Analyze correlation between two metrics."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Metrics Correlation Analysis")
    print("="*60 + "\n")

    client = OrionMCPClient("http://localhost:3030")

    # Analyze correlation between pod latency and CPU usage
    metric1 = "podReadyLatency_P99"
    metric2 = "ovnCPU_avg"
    config = "trt-external-payload-cluster-density.yaml"

    print(f"Analyzing correlation between:")
    print(f"  - {metric1}")
    print(f"  - {metric2}")
    print(f"Configuration: {config}\n")

    result = await client.metrics_correlation(
        metric1=metric1,
        metric2=metric2,
        config=config,
        version="4.20",
        lookback="30"
    )

    if isinstance(result, dict) and result.get("type") == "image":
        # Save correlation plot
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"correlation_{metric1}_vs_{metric2}.jpg"

        image_data = base64.b64decode(result["data"])
        output_path.write_bytes(image_data)
        print(f"Correlation plot saved to: {output_path}")
    else:
        print(f"Result: {result}")


async def example_nightly_regression_detection():
    """Example: Detect regressions in nightly builds."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Nightly Build Regression Detection")
    print("="*60 + "\n")

    client = OrionMCPClient("http://localhost:3030")

    # Check a specific nightly for regressions
    nightly_version = "4.22.0-0.nightly-2026-01-05-203335"

    print(f"Checking nightly version: {nightly_version}")

    result = await client.has_nightly_regressed(
        nightly_version=nightly_version,
        lookback="30"
    )

    print(f"\nResult:\n{result}")

    # Compare two nightlies
    print("\n" + "-"*60)
    print("Comparing two nightly versions...")

    previous_nightly = "4.22.0-0.nightly-2026-01-01-123456"
    current_nightly = "4.22.0-0.nightly-2026-01-05-203335"

    print(f"Previous: {previous_nightly}")
    print(f"Current:  {current_nightly}\n")

    comparison_result = await client.has_nightly_regressed(
        nightly_version=current_nightly,
        previous_nightly=previous_nightly,
        lookback="30"
    )

    print(f"Comparison Result:\n{comparison_result}")


async def example_networking_focus():
    """Example: Focus specifically on networking performance."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Networking Performance Analysis")
    print("="*60 + "\n")

    client = OrionMCPClient("http://localhost:3030")

    # Check for networking-specific regressions
    version = "4.20"
    print(f"Checking networking performance for OpenShift {version}...")

    result = await client.has_networking_regressed(
        version=version,
        lookback="30"
    )

    print(f"\nNetworking Regression Check:\n{result}\n")

    # Get networking-specific metrics
    networking_configs = [
        "small-scale-udn-l3.yaml",
        "trt-external-payload-node-density-cni.yaml"
    ]

    for config in networking_configs:
        print(f"\nMetrics for {config}:")
        metrics = await client.get_orion_metrics(config)
        if isinstance(metrics, dict):
            for config_path, metric_list in metrics.items():
                print(f"  Available metrics: {len(metric_list)}")
                # Print first few metrics
                for metric in metric_list[:5]:
                    print(f"    - {metric}")
                if len(metric_list) > 5:
                    print(f"    ... and {len(metric_list) - 5} more")


async def example_explore_server():
    """Example: Explore server capabilities and resources."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Server Capabilities Discovery")
    print("="*60 + "\n")

    client = OrionMCPClient("http://localhost:3030")

    # List all available tools
    print("Available Tools:")
    tools = await client.list_tools()
    for i, tool in enumerate(tools, 1):
        print(f"\n{i}. {tool['name']}")
        print(f"   Description: {tool['description']}")
        if 'inputSchema' in tool:
            schema = tool['inputSchema']
            if 'properties' in schema:
                print(f"   Parameters:")
                for param_name, param_info in schema['properties'].items():
                    param_desc = param_info.get('description', 'No description')
                    print(f"     - {param_name}: {param_desc}")

    # List all available resources
    print("\n" + "-"*60)
    print("\nAvailable Resources:")
    resources = await client.list_resources()
    for i, resource in enumerate(resources, 1):
        print(f"\n{i}. {resource['uri']}")
        print(f"   Name: {resource.get('name', 'N/A')}")
        print(f"   Description: {resource.get('description', 'N/A')}")

    # Get OpenShift release dates
    print("\n" + "-"*60)
    print("\nOpenShift Release Dates:")
    versions = ["4.17", "4.18", "4.19", "4.20", "4.21", "4.22"]
    for version in versions:
        date = await client.get_release_date(version)
        print(f"  {version}: {date}")


async def main():
    """Run all examples."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "ORION MCP CLIENT EXAMPLES" + " "*18 + "║")
    print("╚" + "="*58 + "╝")

    examples = [
        ("Regression Scan", example_regression_scan),
        ("PR Analysis", example_pr_analysis),
        ("Multi-Version Comparison", example_multi_version_comparison),
        ("Metrics Correlation", example_metrics_correlation),
        ("Nightly Regression Detection", example_nightly_regression_detection),
        ("Networking Focus", example_networking_focus),
        ("Server Exploration", example_explore_server),
    ]

    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nRunning Example 7: Server Exploration...")
    print("(Modify the main() function to run other examples)\n")

    # Run the exploration example by default
    await example_explore_server()

    # Uncomment to run other examples:
    # await example_regression_scan()
    # await example_pr_analysis()
    # await example_multi_version_comparison()
    # await example_metrics_correlation()
    # await example_nightly_regression_detection()
    # await example_networking_focus()


if __name__ == "__main__":
    asyncio.run(main())
