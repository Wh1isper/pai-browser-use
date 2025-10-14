import socket
import time

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
def cdp_url(docker_client):
    """Start headless Chrome container and return CDP URL"""
    chrome_port = get_port()
    image = "zenika/alpine-chrome:latest"
    container = None

    try:
        # Start Chrome container
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
            raise RuntimeError("Chrome container failed to start within timeout")

        yield cdp_endpoint
    finally:
        if container:
            container.stop()
