"""Tests for process replicas feature."""

from procler.config.schema import ProcessDef, ProclerConfig


class TestProcessDefReplicas:
    """Test replicas field on ProcessDef."""

    def test_replicas_default_one(self):
        """ProcessDef defaults to 1 replica."""
        proc = ProcessDef(command="echo hello")
        assert proc.replicas == 1

    def test_replicas_set(self):
        """ProcessDef accepts replicas field."""
        proc = ProcessDef(command="celery worker", replicas=3)
        assert proc.replicas == 3


class TestExpandReplicas:
    """Test ProclerConfig.expand_replicas()."""

    def test_no_replicas(self):
        """Single-replica processes are unchanged."""
        config = ProclerConfig(
            processes={
                "api": ProcessDef(command="uvicorn main:app"),
                "worker": ProcessDef(command="celery worker"),
            }
        )
        expanded = config.expand_replicas()
        assert "api" in expanded
        assert "worker" in expanded
        assert len(expanded) == 2

    def test_expand_three_replicas(self):
        """Process with replicas=3 expands to 3 instances."""
        config = ProclerConfig(
            processes={
                "worker": ProcessDef(command="celery worker", replicas=3),
            }
        )
        expanded = config.expand_replicas()

        assert "worker" not in expanded  # Original name removed
        assert "worker-1" in expanded
        assert "worker-2" in expanded
        assert "worker-3" in expanded
        assert len(expanded) == 3

    def test_expanded_replicas_have_correct_command(self):
        """Each replica keeps the original command."""
        config = ProclerConfig(
            processes={
                "worker": ProcessDef(command="celery worker -A tasks", replicas=2),
            }
        )
        expanded = config.expand_replicas()

        assert expanded["worker-1"].command == "celery worker -A tasks"
        assert expanded["worker-2"].command == "celery worker -A tasks"

    def test_expanded_replicas_have_one_replica(self):
        """Expanded replicas have replicas=1."""
        config = ProclerConfig(
            processes={
                "worker": ProcessDef(command="worker", replicas=3),
            }
        )
        expanded = config.expand_replicas()

        for name in ["worker-1", "worker-2", "worker-3"]:
            assert expanded[name].replicas == 1

    def test_expanded_replicas_get_replica_tag(self):
        """Expanded replicas get a 'replica:{base}' tag."""
        config = ProclerConfig(
            processes={
                "worker": ProcessDef(command="worker", replicas=2, tags=["backend"]),
            }
        )
        expanded = config.expand_replicas()

        assert "replica:worker" in expanded["worker-1"].tags
        assert "backend" in expanded["worker-1"].tags
        assert "replica:worker" in expanded["worker-2"].tags

    def test_mixed_single_and_replicated(self):
        """Mix of single and replicated processes expand correctly."""
        config = ProclerConfig(
            processes={
                "api": ProcessDef(command="uvicorn main:app"),
                "worker": ProcessDef(command="celery worker", replicas=2),
            }
        )
        expanded = config.expand_replicas()

        assert "api" in expanded
        assert "worker-1" in expanded
        assert "worker-2" in expanded
        assert "worker" not in expanded
        assert len(expanded) == 3


class TestGetReplicaNames:
    """Test ProclerConfig.get_replica_names()."""

    def test_single_process(self):
        """Single-replica process returns its own name."""
        config = ProclerConfig(
            processes={
                "api": ProcessDef(command="app"),
            }
        )
        assert config.get_replica_names("api") == ["api"]

    def test_replicated_process(self):
        """Replicated process returns instance names."""
        config = ProclerConfig(
            processes={
                "worker": ProcessDef(command="worker", replicas=3),
            }
        )
        names = config.get_replica_names("worker")
        assert names == ["worker-1", "worker-2", "worker-3"]

    def test_nonexistent_process(self):
        """Non-existent process returns itself."""
        config = ProclerConfig()
        assert config.get_replica_names("ghost") == ["ghost"]


class TestReplicaConfigParsing:
    """Test replicas in YAML config."""

    def test_config_with_replicas(self, tmp_path):
        """Config file with replicas parses correctly."""
        import os

        from procler.config import loader as config_loader

        config_dir = tmp_path / ".procler"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text("""
version: 1

processes:
  api:
    command: uvicorn main:app
  worker:
    command: celery worker
    replicas: 3

groups:
  backend:
    processes: [api, worker]
""")

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        config_loader.reset_config_cache()

        try:
            from procler.config import get_config

            config = get_config()
            assert config.processes["api"].replicas == 1
            assert config.processes["worker"].replicas == 3

            # expand_replicas should work
            expanded = config.expand_replicas()
            assert "worker-1" in expanded
            assert "worker-2" in expanded
            assert "worker-3" in expanded
            assert "api" in expanded
            assert len(expanded) == 4

            # get_replica_names should work
            assert config.get_replica_names("worker") == ["worker-1", "worker-2", "worker-3"]
            assert config.get_replica_names("api") == ["api"]
        finally:
            os.chdir(old_cwd)
            config_loader.reset_config_cache()
