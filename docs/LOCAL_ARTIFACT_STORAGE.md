# Encrypted workspace artifact storage

The current private development installation explicitly selects `ARTIFACT_BACKEND=filesystem`. This is a real persistent encrypted store, not an S3 simulator. JSON artifacts are encrypted using Fernet authenticated encryption, written atomically with mode 0600 beneath `.local/artifacts`, read back/decrypted, and checked against the original SHA-256 before verification. Downloads require the authenticated owner, tenant match, safe URI resolution and checksum verification.

The encryption key lives only in the ignored private environment configuration, not source, prompts, traces or the sandbox. Back up both encrypted files and the key through an approved secret/backup system; losing the key loses access to the artifacts. Do not copy the plaintext key into this repository.

This adapter fails closed when `RUNTIME=production`. The existing private S3 adapter remains the production path. Cloud deployment still requires a privately provisioned S3-compatible bucket and credentials/workload identity. Attempts to pull the official MinIO development image were denied by its registries; no MinIO server or cloud S3 bucket was provisioned or claimed.
