import contextlib
import socket
import time
from pathlib import Path

import docker
import httpx
import pytest


def get_port():
    # Get an unoccupied port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def docker_client():
    try:
        client = docker.from_env()
        client.ping()
        return client
    except:  # noqa: E722
        pytest.skip("Docker is not available")


@pytest.fixture(scope="session")
def docker_network(docker_client):
    """Create a Docker network for test containers"""
    network_name = "pai-test-network"

    # Clean up any existing network with the same name
    with contextlib.suppress(Exception):
        old_network = docker_client.networks.get(network_name)
        old_network.remove()

    network = docker_client.networks.create(network_name, driver="bridge")

    yield network

    # Cleanup network
    with contextlib.suppress(Exception):
        network.remove()


@pytest.fixture(scope="session")
def test_server(docker_client, docker_network):
    """Start Nginx container to serve test HTML files"""
    fixtures_path = Path(__file__).parent / "test_fixtures"

    # Ensure directory exists
    if not fixtures_path.exists():
        pytest.skip("test_fixtures directory not found")

    container = None
    try:
        container = docker_client.containers.run(
            "nginx:alpine",
            detach=True,
            name="test-server",
            network="pai-test-network",
            volumes={
                str(fixtures_path.absolute()): {
                    "bind": "/usr/share/nginx/html/test_fixtures",
                    "mode": "ro",
                }
            },
            remove=True,
        )

        # Wait for nginx to be ready (health check)
        max_retries = 10
        for _ in range(max_retries):
            try:
                # Check from inside the container
                exit_code, _ = container.exec_run("wget -q -O- http://localhost/test_fixtures/basic.html")
                if exit_code == 0:
                    break
            except:  # noqa: E722
                time.sleep(0.5)
        else:
            if container:
                container.stop()
            pytest.fail("Nginx container failed to start")

        # Return the URL accessible from within the Docker network
        yield "http://test-server"

    finally:
        if container:
            with contextlib.suppress(Exception):
                container.stop()


@pytest.fixture(scope="session")
def cdp_url(docker_client, docker_network, test_server):
    """Start headless Chrome container and return CDP URL"""
    chrome_port = get_port()
    image = "zenika/alpine-chrome:latest"
    container = None

    try:
        # Start Chrome container connected to the test network
        container = docker_client.containers.run(
            image,
            command=[
                "chromium-browser",
                "--headless",
                "--remote-debugging-port=9222",
                "--remote-debugging-address=0.0.0.0",
                "--no-sandbox",
            ],
            detach=True,
            name="chrome-test",
            network="pai-test-network",
            ports={"9222": chrome_port},
            remove=True,
        )

        # Wait for Chrome to start and accept connections
        cdp_endpoint = f"http://localhost:{chrome_port}/json/version"
        max_retries = 30
        for _ in range(max_retries):
            try:
                response = httpx.get(cdp_endpoint, timeout=5)
                if response.status_code == 200:
                    break
            except:  # noqa: E722
                time.sleep(1)
        else:
            if container:
                container.stop()
            raise RuntimeError("Chrome container failed to start within timeout")

        yield cdp_endpoint

    finally:
        if container:
            with contextlib.suppress(Exception):
                container.stop()
