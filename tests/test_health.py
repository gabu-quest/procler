"""Tests for health check functionality."""

import asyncio

import pytest

from procler.config import HealthCheckDef
from procler.core.health import (
    HealthState,
    HealthStatus,
    get_health_checker,
    reset_health_checker,
)


def test_health_checker_singleton():
    """Test that HealthChecker is a singleton."""
    checker1 = get_health_checker()
    checker2 = get_health_checker()
    assert checker1 is checker2

    reset_health_checker()
    checker3 = get_health_checker()
    assert checker1 is not checker3


def test_health_state_defaults():
    """Test HealthState default values."""
    state = HealthState(status=HealthStatus.UNKNOWN)
    assert state.status == HealthStatus.UNKNOWN
    assert state.last_check is None
    assert state.consecutive_failures == 0
    assert state.last_error is None
    assert state.check_count == 0


def test_health_status_enum():
    """Test HealthStatus enum values."""
    assert HealthStatus.UNKNOWN.value == "unknown"
    assert HealthStatus.STARTING.value == "starting"
    assert HealthStatus.HEALTHY.value == "healthy"
    assert HealthStatus.UNHEALTHY.value == "unhealthy"
    assert HealthStatus.DEAD.value == "dead"


def test_get_health_unregistered():
    """Test getting health for unregistered process."""
    checker = get_health_checker()
    state = checker.get_health("nonexistent")
    assert state.status == HealthStatus.UNKNOWN


def test_register_process():
    """Test registering a process for health checking."""
    checker = get_health_checker()
    healthcheck = HealthCheckDef(test="echo ok")

    checker.register_process("test-proc", healthcheck)

    state = checker.get_health("test-proc")
    assert state.status == HealthStatus.STARTING


def test_register_process_with_callback():
    """Test registering with status change callback."""
    checker = get_health_checker()
    healthcheck = HealthCheckDef(test="echo ok")

    status_changes = []

    def on_change(proc_name: str, status: HealthStatus):
        status_changes.append((proc_name, status))

    checker.register_process("callback-proc", healthcheck, on_status_change=on_change)
    state = checker.get_health("callback-proc")
    assert state.status == HealthStatus.STARTING


@pytest.mark.asyncio
async def test_run_single_check_success():
    """Test running a single health check that succeeds."""
    checker = get_health_checker()
    healthcheck = HealthCheckDef(test="echo ok", timeout="5s")

    result = await checker.run_single_check("test", healthcheck)

    assert result["success"] is True
    assert result["exit_code"] == 0
    assert "ok" in result["stdout"]
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_run_single_check_failure():
    """Test running a single health check that fails."""
    checker = get_health_checker()
    healthcheck = HealthCheckDef(test="exit 1", timeout="5s")

    result = await checker.run_single_check("test", healthcheck)

    assert result["success"] is False
    assert result["exit_code"] == 1


@pytest.mark.asyncio
async def test_wait_for_healthy_immediate():
    """Test wait_for_healthy with immediate success."""
    checker = get_health_checker()
    healthcheck = HealthCheckDef(test="echo ok", timeout="5s", interval="100ms")

    # Register process first
    checker.register_process("wait-test", healthcheck)

    is_healthy = await checker.wait_for_healthy("wait-test", healthcheck, timeout=5.0)

    assert is_healthy is True
    state = checker.get_health("wait-test")
    assert state.status == HealthStatus.HEALTHY


@pytest.mark.asyncio
async def test_wait_for_healthy_timeout():
    """Test wait_for_healthy times out on failing check."""
    checker = get_health_checker()
    healthcheck = HealthCheckDef(test="exit 1", timeout="1s", interval="100ms")

    is_healthy = await checker.wait_for_healthy("test", healthcheck, timeout=0.5)

    assert is_healthy is False


def test_to_dict():
    """Test health state serialization."""
    checker = get_health_checker()
    healthcheck = HealthCheckDef(test="echo ok")
    checker.register_process("dict-test", healthcheck)

    data = checker.to_dict("dict-test")

    assert data["status"] == "starting"
    assert data["last_check"] is None
    assert data["consecutive_failures"] == 0
    assert data["last_error"] is None
    assert data["check_count"] == 0


def test_to_dict_unregistered():
    """Test to_dict for unregistered process."""
    checker = get_health_checker()
    data = checker.to_dict("nonexistent")

    assert data["status"] == "unknown"


@pytest.mark.asyncio
async def test_stop_checking():
    """Test stopping health checks."""
    checker = get_health_checker()
    healthcheck = HealthCheckDef(test="echo ok", interval="100ms")
    checker.register_process("stop-test", healthcheck)

    # Start and immediately stop
    await checker.start_checking("stop-test", healthcheck)
    await asyncio.sleep(0.05)  # Let it start
    await checker.stop_checking("stop-test")

    state = checker.get_health("stop-test")
    assert state.status == HealthStatus.DEAD


def test_reset():
    """Test resetting the health checker."""
    checker = get_health_checker()
    healthcheck = HealthCheckDef(test="echo ok")
    checker.register_process("reset-test", healthcheck)

    checker.reset()

    state = checker.get_health("reset-test")
    assert state.status == HealthStatus.UNKNOWN


# HealthCheckDef parsing tests


def test_healthcheck_def_defaults():
    """Test HealthCheckDef default values."""
    hc = HealthCheckDef(test="curl localhost")

    assert hc.test == "curl localhost"
    assert hc.interval == "10s"
    assert hc.timeout == "5s"
    assert hc.retries == 3
    assert hc.start_period == "0s"


def test_healthcheck_get_interval_seconds():
    """Test parsing interval to seconds."""
    assert HealthCheckDef(test="x", interval="10s").get_interval_seconds() == 10.0
    assert HealthCheckDef(test="x", interval="500ms").get_interval_seconds() == 0.5
    assert HealthCheckDef(test="x", interval="2m").get_interval_seconds() == 120.0
    # Note: hours not supported, use minutes (e.g., "60m" instead of "1h")


def test_healthcheck_get_timeout_seconds():
    """Test parsing timeout to seconds."""
    assert HealthCheckDef(test="x", timeout="5s").get_timeout_seconds() == 5.0
    assert HealthCheckDef(test="x", timeout="100ms").get_timeout_seconds() == 0.1


def test_healthcheck_get_start_period_seconds():
    """Test parsing start_period to seconds."""
    assert HealthCheckDef(test="x", start_period="0s").get_start_period_seconds() == 0.0
    assert HealthCheckDef(test="x", start_period="30s").get_start_period_seconds() == 30.0
    assert HealthCheckDef(test="x", start_period="1m").get_start_period_seconds() == 60.0
