"""
Component actions CLI use case.
"""

import logging

from core.domain.value_objects.component_action_request import (
    ComponentActionRequest as CoreActionRequest,
)
from core.domain.value_objects.get_component_actions_request import (
    GetComponentActionsRequest,
)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cli.dependencies.container import CLIContainer
from cli.entities.component_actions import (
    ComponentActionRequest,
    ComponentActionResult,
    ComponentActionsListRequest,
    ComponentActionsListResult,
)

from ..common.progress_tracking import ProgressTracker
from ..common.result_formatting import ResultFormatter

logger = logging.getLogger(__name__)


class ComponentActionsUseCase:
    """Unified CLI use case for all component actions."""

    def __init__(self, container: CLIContainer, console: Console):
        self._container = container
        self._console = console
        self._progress_tracker = ProgressTracker(console)
        self._result_formatter = ResultFormatter(console)

    async def execute_action(
        self, request: ComponentActionRequest
    ) -> list[ComponentActionResult]:
        """Execute component action on multiple devices with progress tracking.

        Args:
            request: Component action request

        Returns:
            List of component action results
        """
        if request.from_config:
            config_gateway = self._container.get_config_gateway()
            device_ips = await config_gateway.get_predefined_ips()
        elif request.devices:
            device_ips = request.devices
        else:
            raise ValueError(
                "No devices specified. Provide device IPs or use --from-config"
            )

        if not device_ips:
            raise ValueError("No devices found")

        if not request.force:
            action_desc = f"{request.action} on {request.component_key}"
            device_list = ", ".join(device_ips[:3]) + (
                f" and {len(device_ips)-3} more" if len(device_ips) > 3 else ""
            )

            self._console.print(f"\n[yellow]About to execute:[/yellow] {action_desc}")
            self._console.print(f"[yellow]Target devices:[/yellow] {device_list}")

            if not self._console.input("\nContinue? [y/N]: ").lower().startswith("y"):
                raise RuntimeError("Operation cancelled by user")

        results = []
        execute_interactor = self._container.get_execute_component_action_interactor()

        async with self._progress_tracker.track_progress(
            f"Executing {request.action} on {request.component_key}",
            total=len(device_ips),
        ) as progress:
            for device_ip in device_ips:
                try:
                    core_request = CoreActionRequest(
                        device_ip=device_ip,
                        component_key=request.component_key,
                        action=request.action,
                        parameters=request.parameters,
                    )

                    action_result = await execute_interactor.execute(core_request)

                    result = ComponentActionResult(
                        ip=device_ip,
                        status="success" if action_result.success else "failed",
                        component_key=request.component_key,
                        action=request.action,
                        parameters=request.parameters,
                        message=action_result.message,
                        error=action_result.error,
                        action_successful=action_result.success,
                        action_data=action_result.data,
                    )
                    results.append(result)

                except Exception as e:
                    result = ComponentActionResult(
                        ip=device_ip,
                        status="error",
                        component_key=request.component_key,
                        action=request.action,
                        parameters=request.parameters,
                        message=f"Failed to execute {request.action}",
                        error=str(e),
                        action_successful=False,
                    )
                    results.append(result)

                progress.advance()

        return results

    async def list_actions(
        self, request: ComponentActionsListRequest
    ) -> list[ComponentActionsListResult]:
        """List available component actions for devices.

        Args:
            request: Component actions list request

        Returns:
            List of component actions list results
        """
        if request.from_config:
            config_gateway = self._container.get_config_gateway()
            device_ips = await config_gateway.get_predefined_ips()
        elif request.devices:
            device_ips = request.devices
        else:
            raise ValueError(
                "No devices specified. Provide device IPs or use --from-config"
            )

        if not device_ips:
            raise ValueError("No devices found")

        results = []
        actions_interactor = self._container.get_component_actions_interactor()

        async with self._progress_tracker.track_progress(
            "Getting available actions", total=len(device_ips)
        ) as progress:
            for device_ip in device_ips:
                try:
                    core_request = GetComponentActionsRequest(device_ip=device_ip)
                    actions = await actions_interactor.execute(core_request)

                    if request.component_type:
                        filtered_actions = {
                            k: v
                            for k, v in actions.items()
                            if k.startswith(request.component_type)
                        }
                        actions = filtered_actions

                    result = ComponentActionsListResult(
                        ip=device_ip,
                        status="success",
                        message="Actions retrieved successfully",
                        available_actions=actions,
                    )
                    results.append(result)

                except Exception as e:
                    logger.error(f"Failed to get actions for {device_ip}: {e}")
                    result = ComponentActionsListResult(
                        ip=device_ip,
                        status="error",
                        message="Failed to get actions",
                        error=str(e),
                        available_actions={},
                    )
                    results.append(result)

                progress.advance()

        return results

    def display_action_results(self, results: list[ComponentActionResult]) -> None:
        """Display component action results in Rich table.

        Args:
            results: List of component action results to display
        """
        if not results:
            self._console.print("\n[yellow]No results to display[/yellow]")
            return

        first_result = results[0]
        title = f"Component Action Results: {first_result.component_key}.{first_result.action}"
        if first_result.parameters:
            params_str = ", ".join(
                f"{k}={v}" for k, v in first_result.parameters.items()
            )
            title += f" ({params_str})"

        table = Table(title=title)
        table.add_column("Device IP", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Message", style="white")

        successful = 0
        for result in results:
            status = (
                "[green]✓ Success[/green]"
                if result.action_successful
                else "[red]✗ Failed[/red]"
            )
            if result.action_successful:
                successful += 1

            table.add_row(
                result.ip,
                status,
                result.message or "No message",
            )

        self._console.print()
        self._console.print(table)

        total = len(results)
        failed = total - successful
        summary = f"[green]{successful} successful[/green]"
        if failed > 0:
            summary += f", [red]{failed} failed[/red]"
        summary += f" out of {total} devices"

        self._console.print(f"\n{summary}")

    def display_actions_list(self, results: list[ComponentActionsListResult]) -> None:
        """Display available component actions in Rich panels.

        Args:
            results: List of component actions list results to display
        """
        if not results:
            self._console.print("\n[yellow]No results to display[/yellow]")
            return

        for result in results:
            if not result.status == "success":
                self._console.print(
                    f"\n[red]Failed to get actions for {result.ip}: {result.error}[/red]"
                )
                continue

            if not result.available_actions:
                self._console.print(
                    f"\n[yellow]No actions available for {result.ip}[/yellow]"
                )
                continue

            content = []
            for component_key, actions in result.available_actions.items():
                if actions:
                    actions_str = ", ".join(actions)
                    content.append(f"[cyan]{component_key}[/cyan]: {actions_str}")
                else:
                    content.append(
                        f"[cyan]{component_key}[/cyan]: [dim]No actions available[/dim]"
                    )

            panel = Panel(
                "\n".join(content),
                title=f"[bold]Available Actions - {result.ip}[/bold]",
                expand=False,
                border_style="blue",
            )
            self._console.print(panel)
