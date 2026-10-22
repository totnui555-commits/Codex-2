import json

import pytest
from company_os.providers import ArtifactStore, IntegrationBlocked
from company_os.settings import settings
from cryptography.fernet import Fernet


def test_real_encrypted_artifact_roundtrip_and_tamper(tmp_path, monkeypatch):
    s = settings()
    for key, value in {
        "artifact_backend": "filesystem",
        "artifact_directory": str(tmp_path),
        "artifact_encryption_key": Fernet.generate_key().decode(),
        "runtime": "development",
    }.items():
        monkeypatch.setattr(s, key, value)
    store = ArtifactStore()
    uri, checksum = store.put("org", "task", "report", {"verified": "private content"})
    assert json.loads(store.read(uri, checksum)) == {"verified": "private content"}
    file = next(tmp_path.rglob("*.fernet"))
    assert b"private content" not in file.read_bytes()
    assert file.stat().st_mode & 0o777 == 0o600
    with pytest.raises(ValueError):
        store.read(uri, "0" * 64)
    with pytest.raises(IntegrationBlocked):
        store.read("private-file://../../escape", checksum)


def test_local_artifacts_denied_in_production(tmp_path, monkeypatch):
    s = settings()
    monkeypatch.setattr(s, "artifact_backend", "filesystem")
    monkeypatch.setattr(s, "runtime", "production")
    monkeypatch.setattr(s, "artifact_encryption_key", Fernet.generate_key().decode())
    with pytest.raises(IntegrationBlocked):
        ArtifactStore()
