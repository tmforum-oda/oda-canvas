"""
Helm API Wrapper for TMF639 Resource Inventory MCP Server

This module provides a Python wrapper around Helm CLI commands to enable
MCP clients to manage Helm charts from the TM Forum ODA repository.

Based on the patterns from:
- feature-definition-and-test-kit/package-manager-utils-helm/package-manager-utils-helm.js
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import time
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
HELM_COMMAND_DELAY = 2.0  # seconds
DEFAULT_HELM_REPO_NAME = "oda-components"
DEFAULT_HELM_REPO_URL = "https://tmforum-oda.github.io/reference-example-components"


class HelmReleaseStatus(Enum):
    """Helm release status enumeration"""
    DEPLOYED = "deployed"
    FAILED = "failed"
    PENDING_INSTALL = "pending-install"
    PENDING_UPGRADE = "pending-upgrade"
    PENDING_ROLLBACK = "pending-rollback"
    SUPERSEDED = "superseded"
    UNINSTALLING = "uninstalling"
    UNKNOWN = "unknown"


@dataclass
class HelmRelease:
    """Represents a Helm release"""
    name: str
    namespace: str
    revision: str
    updated: str
    status: str
    chart: str
    app_version: str = ""


@dataclass
class HelmRepository:
    """Represents a Helm repository"""
    name: str
    url: str


class HelmAPIError(Exception):
    """Custom exception for Helm API errors"""
    pass


class HelmAPI:
    """
    Python wrapper for Helm CLI commands specifically designed for 
    TM Forum ODA Component management via MCP protocol.
    """

    def __init__(self, helm_command: str = "helm"):
        """
        Initialize Helm API wrapper.
        
        Args:
            helm_command: Path to helm binary (default: "helm")
        """
        self.helm_command = helm_command
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def _execute_helm_command(self, command: List[str], capture_output: bool = True) -> str:
        """
        Execute a Helm command asynchronously.
        
        Args:
            command: List of command parts
            capture_output: Whether to capture and return output
            
        Returns:
            Command output as string
            
        Raises:
            HelmAPIError: If command fails
        """
        full_command = [self.helm_command] + command
        command_str = " ".join(full_command)
        
        self.logger.info(f"Executing: {command_str}")
        
        try:
            if capture_output:
                process = await asyncio.create_subprocess_exec(
                    *full_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    error_msg = f"Helm command failed: {command_str}\nError: {stderr.decode()}"
                    self.logger.error(error_msg)
                    raise HelmAPIError(error_msg)
                
                output = stdout.decode().strip()
                self.logger.info(f"Helm output: {output}")
                
                # Add delay to avoid race conditions
                await asyncio.sleep(HELM_COMMAND_DELAY)
                
                return output
            else:
                process = await asyncio.create_subprocess_exec(*full_command)
                await process.wait()
                
                if process.returncode != 0:
                    error_msg = f"Helm command failed: {command_str}"
                    self.logger.error(error_msg)
                    raise HelmAPIError(error_msg)
                
                await asyncio.sleep(HELM_COMMAND_DELAY)
                return ""
                
        except FileNotFoundError:
            error_msg = f"Helm binary not found: {self.helm_command}"
            self.logger.error(error_msg)
            raise HelmAPIError(error_msg)
        except Exception as e:
            error_msg = f"Failed to execute helm command: {command_str}. Error: {str(e)}"
            self.logger.error(error_msg)
            raise HelmAPIError(error_msg)

    async def add_repository(self, repository: str, repo_url: str) -> Dict[str, Any]:
        """
        Add a Helm repository.
        
        Args:
            repository: Name of the repository
            repo_url: URL of the repository
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Check if repo already exists
            existing_repos = await self.list_repositories()
            for repo in existing_repos:
                if repo.name == repository and repo.url == repo_url:
                    self.logger.info(f"Repository '{repository}' already exists")
                    return {
                        "success": True,
                        "message": f"Repository '{repository}' already exists",
                        "repository": repository,
                        "repo_url": repo_url,
                        "action": "already_exists"
                    }
            
            # Add repository
            await self._execute_helm_command(["repo", "add", repository, repo_url])
            
            self.logger.info(f"Successfully added repository '{repository}'")
            return {
                "success": True,
                "message": f"Successfully added repository '{repository}'",
                "repository": repository,
                "repo_url": repo_url,
                "action": "added"
            }
            
        except HelmAPIError as e:
            self.logger.error(f"Failed to add repository '{repository}': {e}")
            return {
                "success": False,
                "error": str(e),
                "repository": repository,
                "repo_url": repo_url
            }

    async def update_repositories(self, repository: Optional[str] = None) -> Dict[str, Any]:
        """
        Update Helm repositories.
        
        Args:
            repository: Specific repository to update (optional)
            
        Returns:
            Dictionary with operation result
        """
        try:
            if repository:
                await self._execute_helm_command(["repo", "update", repository])
                message = f"Successfully updated repository '{repository}'"
            else:
                await self._execute_helm_command(["repo", "update"])
                message = "Successfully updated all repositories"
            
            self.logger.info(message)
            return {
                "success": True,
                "message": message,
                "repository": repository
            }
            
        except HelmAPIError as e:
            error_msg = f"Failed to update repositories: {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": str(e),
                "repository": repository
            }

    async def list_repositories(self) -> List[HelmRepository]:
        """
        List all Helm repositories.
        
        Returns:
            List of HelmRepository objects
        """
        try:
            output = await self._execute_helm_command(["repo", "list", "-o", "json"])
            if not output.strip():
                return []
            
            repos_data = json.loads(output)
            repositories = [
                HelmRepository(name=repo["name"], url=repo["url"])
                for repo in repos_data            ]
            
            self.logger.info(f"Found {len(repositories)} repositories")
            return repositories
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse repositories JSON: {e}")
            return []
        except HelmAPIError as e:
            self.logger.error(f"Failed to list repositories: {e}")
            return []

    async def search_charts(self, search_term: Optional[str] = None, repository: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for Helm charts.
        
        Args:
            search_term: Term to search for (if None, searches for all charts)
            repository: Specific repository to search (optional)
            
        Returns:
            List of chart information
        """
        try:
            # If search_term is None, search for all charts
            if search_term is None:
                search_term = "*"
                
            command = ["search", "repo"]
            if repository:
                command.append(f"{repository}/{search_term}")
            else:
                command.append(search_term)
            
            command.extend(["-o", "json"])
            
            output = await self._execute_helm_command(command)
            if not output.strip():
                return []
            
            charts = json.loads(output)
            self.logger.info(f"Found {len(charts)} charts matching '{search_term}'")
            return charts
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse search results JSON: {e}")
            return []
        except HelmAPIError as e:
            self.logger.error(f"Failed to search charts: {e}")
            return []

    async def list_releases(self, namespace: str = "components") -> List[HelmRelease]:
        """
        List Helm releases in a namespace.
        
        Args:
            namespace: Kubernetes namespace
            
        Returns:
            List of HelmRelease objects
        """
        try:
            output = await self._execute_helm_command(["list", "-o", "json", "-n", namespace])
            if not output.strip():
                return []
            
            releases_data = json.loads(output)
            releases = [
                HelmRelease(
                    name=release["name"],
                    namespace=release["namespace"],
                    revision=release["revision"],
                    updated=release["updated"],
                    status=release["status"],
                    chart=release["chart"],
                    app_version=release.get("app_version", "")
                )
                for release in releases_data
            ]
            self.logger.info(f"Found {len(releases)} releases in namespace '{namespace}'")
            return releases
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse releases JSON: {e}")
            return []
        except HelmAPIError as e:
            self.logger.error(f"Failed to list releases: {e}")
            return []

    async def install_chart(
        self,
        release_name: str,
        chart_name: str,
        namespace: str = "components",
        repository: Optional[str] = None,
        values: Optional[Dict[str, Any]] = None,
        create_namespace: bool = True,
        chart_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Install a Helm chart.
        
        Args:
            release_name: Name for the release
            chart_name: Name of the chart to install
            namespace: Kubernetes namespace
            repository: Repository name (if installing from repo)
            values: Values to override
            create_namespace: Whether to create namespace if it doesn't exist
            chart_version: Specific chart version to install
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Check if release already exists
            existing_releases = await self.list_releases(namespace)
            for release in existing_releases:
                if release.name == release_name:
                    return {
                        "success": False,
                        "error": f"Release '{release_name}' already exists in namespace '{namespace}'",
                        "release_name": release_name,
                        "namespace": namespace,
                        "action": "already_exists"
                    }
            
            # Build install command
            command = ["install", release_name]
            
            if repository:
                command.append(f"{repository}/{chart_name}")
            else:
                command.append(chart_name)
            
            command.extend(["-n", namespace])
            
            if create_namespace:
                command.append("--create-namespace")
            
            # Add chart version if specified
            if chart_version:
                command.extend(["--version", chart_version])
            
            # Handle values
            values_file_path = None
            if values:
                # Check if values contain complex nested structures
                has_complex_values = any(isinstance(v, (dict, list)) for v in values.values())
                
                if has_complex_values:
                    # Use values file for complex structures
                    values_file_path = await self._create_values_file(values)
                    command.extend(["-f", values_file_path])
                else:
                    # Use --set for simple key-value pairs
                    for key, value in values.items():
                        command.extend(["--set", f"{key}={value}"])
            
            try:
                await self._execute_helm_command(command)
            finally:
                # Clean up temporary values file if created
                if values_file_path and os.path.exists(values_file_path):
                    try:
                        os.unlink(values_file_path)
                        self.logger.info(f"Cleaned up temporary values file: {values_file_path}")
                    except OSError as e:
                        self.logger.warning(f"Failed to clean up values file {values_file_path}: {e}")
            
            message = f"Successfully installed chart '{chart_name}' as release '{release_name}'"
            self.logger.info(message)
            return {
                "success": True,
                "message": message,
                "release_name": release_name,
                "chart_name": chart_name,
                "namespace": namespace,
                "action": "installed"
            }
            
        except HelmAPIError as e:
            error_msg = f"Failed to install chart '{chart_name}': {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": str(e),
                "release_name": release_name,
                "chart_name": chart_name,
                "namespace": namespace
            }

    async def upgrade_chart(
        self,
        release_name: str,
        chart_name: str,
        namespace: str = "components",
        repository: Optional[str] = None,
        values: Optional[Dict[str, Any]] = None,
        chart_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upgrade a Helm release.
        
        Args:
            release_name: Name of the release to upgrade
            chart_name: Name of the chart
            namespace: Kubernetes namespace
            repository: Repository name (if upgrading from repo)
            values: Values to override
            chart_version: Specific chart version to upgrade to
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Check if release exists
            existing_releases = await self.list_releases(namespace)
            release_exists = any(release.name == release_name for release in existing_releases)
            
            if not release_exists:
                return {
                    "success": False,
                    "error": f"Release '{release_name}' not found in namespace '{namespace}'",
                    "release_name": release_name,
                    "namespace": namespace
                }
            
            # Build upgrade command
            command = ["upgrade", release_name]
            
            if repository:
                command.append(f"{repository}/{chart_name}")
            else:
                command.append(chart_name)
            
            command.extend(["-n", namespace])
            
            # Add chart version if specified
            if chart_version:
                command.extend(["--version", chart_version])
            
            # Handle values
            values_file_path = None
            if values:
                # Check if values contain complex nested structures
                has_complex_values = any(isinstance(v, (dict, list)) for v in values.values())
                
                if has_complex_values:
                    # Use values file for complex structures
                    values_file_path = await self._create_values_file(values)
                    command.extend(["-f", values_file_path])
                else:
                    # Use --set for simple key-value pairs
                    for key, value in values.items():
                        command.extend(["--set", f"{key}={value}"])
            
            try:
                await self._execute_helm_command(command)
            finally:
                # Clean up temporary values file if created
                if values_file_path and os.path.exists(values_file_path):
                    try:
                        os.unlink(values_file_path)
                        self.logger.info(f"Cleaned up temporary values file: {values_file_path}")
                    except OSError as e:
                        self.logger.warning(f"Failed to clean up values file {values_file_path}: {e}")
            
            message = f"Successfully upgraded release '{release_name}'"
            self.logger.info(message)
            return {
                "success": True,
                "message": message,
                "release_name": release_name,
                "chart_name": chart_name,
                "namespace": namespace,
                "action": "upgraded"
            }
            
        except HelmAPIError as e:
            error_msg = f"Failed to upgrade release '{release_name}': {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": str(e),
                "release_name": release_name,
                "chart_name": chart_name,
                "namespace": namespace
            }

    async def uninstall_release(self, release_name: str, namespace: str = "components") -> Dict[str, Any]:
        """
        Uninstall a Helm release.
        
        Args:
            release_name: Name of the release to uninstall
            namespace: Kubernetes namespace
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Check if release exists
            existing_releases = await self.list_releases(namespace)
            release_exists = any(release.name == release_name for release in existing_releases)
            
            if not release_exists:
                return {
                    "success": False,
                    "error": f"Release '{release_name}' not found in namespace '{namespace}'",
                    "release_name": release_name,
                    "namespace": namespace
                }
            
            await self._execute_helm_command(["uninstall", release_name, "-n", namespace])
            
            message = f"Successfully uninstalled release '{release_name}'"
            self.logger.info(message)
            return {
                "success": True,
                "message": message,
                "release_name": release_name,
                "namespace": namespace,
                "action": "uninstalled"
            }
            
        except HelmAPIError as e:
            error_msg = f"Failed to uninstall release '{release_name}': {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": str(e),
                "release_name": release_name,
                "namespace": namespace
            }

    async def get_release_status(self, release_name: str, namespace: str = "components") -> Dict[str, Any]:
        """
        Get the status of a Helm release.
        
        Args:
            release_name: Name of the release
            namespace: Kubernetes namespace
            
        Returns:
            Dictionary with release status information
        """
        try:
            output = await self._execute_helm_command(["status", release_name, "-n", namespace, "-o", "json"])
            status_data = json.loads(output)
            
            return {
                "success": True,
                "release_name": release_name,
                "namespace": namespace,
                "status": status_data
            }
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse status JSON: {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "release_name": release_name,
                "namespace": namespace
            }
        except HelmAPIError as e:
            error_msg = f"Failed to get status for release '{release_name}': {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": str(e),
                "release_name": release_name,
                "namespace": namespace
            }

    async def install_or_upgrade_chart(
        self,
        release_name: str,
        chart_name: str,
        namespace: str = "components",
        repository: Optional[str] = None,
        values: Optional[Dict[str, Any]] = None,
        create_namespace: bool = True
    ) -> Dict[str, Any]:
        """
        Install a chart if it doesn't exist, otherwise upgrade it.
        
        Args:
            release_name: Name for the release
            chart_name: Name of the chart
            namespace: Kubernetes namespace
            repository: Repository name (if installing from repo)
            values: Values to override
            create_namespace: Whether to create namespace if it doesn't exist
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Check if release exists
            existing_releases = await self.list_releases(namespace)
            release_exists = any(release.name == release_name for release in existing_releases)
            
            if release_exists:
                return await self.upgrade_chart(
                    release_name=release_name,
                    chart_name=chart_name,
                    namespace=namespace,
                    repository=repository,
                    values=values
                )
            else:
                return await self.install_chart(
                    release_name=release_name,
                    chart_name=chart_name,
                    namespace=namespace,
                    repository=repository,
                    values=values,
                    create_namespace=create_namespace
                )
                
        except Exception as e:
            error_msg = f"Failed to install or upgrade chart '{chart_name}': {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": str(e),
                "release_name": release_name,
                "chart_name": chart_name,
                "namespace": namespace
            }

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, str]:
        """
        Flatten a nested dictionary for use with Helm --set flags.
        
        Args:
            d: Dictionary to flatten
            parent_key: Parent key for recursion
            sep: Separator for nested keys
            
        Returns:
            Flattened dictionary with dot-notation keys
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Handle lists by creating indexed keys
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                    else:
                        items.append((f"{new_key}[{i}]", str(item)))
            else:
                items.append((new_key, str(v)))
        return dict(items)

    async def _create_values_file(self, values: Dict[str, Any]) -> str:
        """
        Create a temporary values file for complex value structures.
        
        Args:
            values: Values dictionary to write to file
            
        Returns:
            Path to temporary values file
        """
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        try:
            yaml.dump(values, temp_file, default_flow_style=False)
            temp_file.flush()
            self.logger.info(f"Created temporary values file: {temp_file.name}")
            return temp_file.name
        finally:
            temp_file.close()


# Convenience functions for TM Forum ODA repository
async def setup_tmforum_oda_repo(helm_api: HelmAPI) -> Dict[str, Any]:
    """
    Setup TM Forum ODA Helm repository.
    
    Args:
        helm_api: HelmAPI instance
        
    Returns:
        Dictionary with operation result
    """
    return await helm_api.add_repository(DEFAULT_HELM_REPO_NAME, DEFAULT_HELM_REPO_URL)


async def update_tmforum_oda_repo(helm_api: HelmAPI) -> Dict[str, Any]:
    """
    Update TM Forum ODA Helm repository.
    
    Args:
        helm_api: HelmAPI instance
        
    Returns:
        Dictionary with operation result
    """
    return await helm_api.update_repositories(DEFAULT_HELM_REPO_NAME)


async def search_tmforum_oda_charts(helm_api: HelmAPI, search_term: str = "") -> List[Dict[str, Any]]:
    """
    Search TM Forum ODA charts.
    
    Args:
        helm_api: HelmAPI instance
        search_term: Search term (empty for all charts)
        
    Returns:
        List of chart information
    """
    return await helm_api.search_charts(search_term or "*", DEFAULT_HELM_REPO_NAME)


# Example usage and testing
async def main():
    """Example usage of HelmAPI"""
    helm_api = HelmAPI()
    
    try:
        # Setup TM Forum ODA repository
        print("Setting up TM Forum ODA repository...")
        result = await setup_tmforum_oda_repo(helm_api)
        print(f"Setup result: {result}")
        
        # Update repositories
        print("\nUpdating repositories...")
        result = await update_tmforum_oda_repo(helm_api)
        print(f"Update result: {result}")
        
        # Search for charts
        print("\nSearching for charts...")
        charts = await search_tmforum_oda_charts(helm_api)
        print(f"Found {len(charts)} charts")
        for chart in charts[:3]:  # Show first 3
            print(f"  - {chart['name']}: {chart['description']}")
        
        # List current releases
        print("\nListing current releases...")
        releases = await helm_api.list_releases("components")
        print(f"Found {len(releases)} releases")
        for release in releases:
            print(f"  - {release.name} ({release.status})")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
