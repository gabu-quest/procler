"""Tests for HTTP/TCP readiness probes."""

import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from pydantic import ValidationError

from procler.config.schema import HealthCheckDef
from procler.core.health import get_health_checker


class TestHealthCheckDefValidation:
    """Test HealthCheckDef validation for probe types."""

    def test_command_probe(self):
        """Command probe is valid."""
        hc = HealthCheckDef(test="curl -f http://localhost/health")
        assert hc.test == "curl -f http://localhost/health"
        assert hc.http_get is None
        assert hc.tcp_socket is None

    def test_http_probe(self):
        """HTTP probe is valid."""
        hc = HealthCheckDef(http_get="http://localhost:8000/health")
        assert hc.http_get == "http://localhost:8000/health"
        assert hc.test is None
        assert hc.tcp_socket is None

    def test_tcp_probe(self):
        """TCP probe is valid."""
        hc = HealthCheckDef(tcp_socket="localhost:5432")
        assert hc.tcp_socket == "localhost:5432"
        assert hc.test is None
        assert hc.http_get is None

    def test_no_probe_raises(self):
        """No probe type specified raises validation error."""
        with pytest.raises(ValidationError, match="must specify one of"):
            HealthCheckDef()

    def test_multiple_probes_raises(self):
        """Multiple probe types raises validation error."""
        with pytest.raises(ValidationError, match="must specify only one"):
            HealthCheckDef(test="curl localhost", http_get="http://localhost/health")

    def test_all_three_probes_raises(self):
        """All three probe types raises validation error."""
        with pytest.raises(ValidationError, match="must specify only one"):
            HealthCheckDef(
                test="curl localhost",
                http_get="http://localhost/health",
                tcp_socket="localhost:5432",
            )

    def test_http_and_tcp_raises(self):
        """HTTP + TCP probe raises validation error."""
        with pytest.raises(ValidationError, match="must specify only one"):
            HealthCheckDef(http_get="http://localhost/health", tcp_socket="localhost:5432")


class TestHTTPProbe:
    """Test HTTP GET health check probe."""

    @pytest.fixture
    def http_server(self):
        """Start a temporary HTTP server for testing."""

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/health":
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"OK")
                elif self.path == "/error":
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b"Error")
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                pass  # Suppress server logs in test output

        server = HTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        yield port
        server.shutdown()

    async def test_http_probe_success(self, http_server):
        """HTTP probe succeeds with 200 status."""
        checker = get_health_checker()
        success, error = await checker._check_http(f"http://127.0.0.1:{http_server}/health", timeout=5.0)
        assert success is True
        assert error == ""

    async def test_http_probe_failure_500(self, http_server):
        """HTTP probe fails with 500 status."""
        checker = get_health_checker()
        success, error = await checker._check_http(f"http://127.0.0.1:{http_server}/error", timeout=5.0)
        assert success is False
        assert "500" in error or "Server Error" in error

    async def test_http_probe_connection_refused(self):
        """HTTP probe fails when server is not running."""
        checker = get_health_checker()
        success, error = await checker._check_http("http://127.0.0.1:59999/health", timeout=2.0)
        assert success is False
        assert error != ""

    async def test_run_check_routes_to_http(self, http_server):
        """_run_check correctly routes to HTTP probe."""
        checker = get_health_checker()
        hc = HealthCheckDef(http_get=f"http://127.0.0.1:{http_server}/health", timeout="5s")
        success, stdout, stderr = await checker._run_check(hc)
        assert success is True


class TestTCPProbe:
    """Test TCP socket health check probe."""

    @pytest.fixture
    def tcp_server(self):
        """Start a temporary TCP server for testing."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]

        def accept_connections():
            while True:
                try:
                    conn, _ = server.accept()
                    conn.close()
                except OSError:
                    break

        thread = threading.Thread(target=accept_connections)
        thread.daemon = True
        thread.start()
        yield port
        server.close()

    async def test_tcp_probe_success(self, tcp_server):
        """TCP probe succeeds when port is open."""
        checker = get_health_checker()
        success, error = await checker._check_tcp(f"127.0.0.1:{tcp_server}", timeout=5.0)
        assert success is True
        assert error == ""

    async def test_tcp_probe_connection_refused(self):
        """TCP probe fails when port is closed."""
        checker = get_health_checker()
        success, error = await checker._check_tcp("127.0.0.1:59998", timeout=2.0)
        assert success is False
        assert error != ""

    async def test_tcp_probe_invalid_address(self):
        """TCP probe fails with invalid address (no port)."""
        checker = get_health_checker()
        success, error = await checker._check_tcp("localhost", timeout=2.0)
        assert success is False
        assert "missing port" in error.lower()

    async def test_run_check_routes_to_tcp(self, tcp_server):
        """_run_check correctly routes to TCP probe."""
        checker = get_health_checker()
        hc = HealthCheckDef(tcp_socket=f"127.0.0.1:{tcp_server}", timeout="5s")
        success, stdout, stderr = await checker._run_check(hc)
        assert success is True


class TestRunCheckRouting:
    """Test that _run_check routes to the correct probe type."""

    async def test_command_probe_routing(self):
        """_run_check routes to command exec for test probe."""
        checker = get_health_checker()
        hc = HealthCheckDef(test="echo ok", timeout="5s")
        success, stdout, stderr = await checker._run_check(hc)
        assert success is True

    async def test_command_probe_failure(self):
        """_run_check reports failure for failing command."""
        checker = get_health_checker()
        hc = HealthCheckDef(test="false", timeout="5s")
        success, stdout, stderr = await checker._run_check(hc)
        assert success is False


class TestProbeConfigParsing:
    """Test probe types in YAML config."""

    def test_config_with_http_probe(self, tmp_path):
        """Config file with http_get probe parses correctly."""
        import os

        from procler.config import loader as config_loader

        config_dir = tmp_path / ".procler"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text("""
version: 1

processes:
  api:
    command: uvicorn main:app
    healthcheck:
      http_get: http://localhost:8000/health
      interval: 5s
      timeout: 2s
      retries: 3
""")

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        config_loader.reset_config_cache()

        try:
            from procler.config import get_config

            config = get_config()
            hc = config.processes["api"].healthcheck
            assert hc is not None
            assert hc.http_get == "http://localhost:8000/health"
            assert hc.test is None
            assert hc.tcp_socket is None
            assert hc.get_interval_seconds() == 5.0
        finally:
            os.chdir(old_cwd)
            config_loader.reset_config_cache()

    def test_config_with_tcp_probe(self, tmp_path):
        """Config file with tcp_socket probe parses correctly."""
        import os

        from procler.config import loader as config_loader

        config_dir = tmp_path / ".procler"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text("""
version: 1

processes:
  db:
    command: postgres
    context: docker
    container: my-postgres
    healthcheck:
      tcp_socket: localhost:5432
      interval: 10s
""")

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        config_loader.reset_config_cache()

        try:
            from procler.config import get_config

            config = get_config()
            hc = config.processes["db"].healthcheck
            assert hc is not None
            assert hc.tcp_socket == "localhost:5432"
            assert hc.test is None
            assert hc.http_get is None
        finally:
            os.chdir(old_cwd)
            config_loader.reset_config_cache()
