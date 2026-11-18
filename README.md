# 🛡️ AegisVault: Zero-Knowledge Digital Will & Dead-Man's Switch

A containerized emergency continuity platform built for **Collaborative Development and DevOps (1BCS303)**.

## 🚀 Key Architecture & Features
- **Zero-Knowledge Split-Key Security:** Encrypts plain-text passwords using AES-128-CBC (`Fernet`) and splits the master key via cryptographic XOR into **Share A** (Server) and **Share B** (Beneficiary Offline Key).
- **Multi-Container Docker Compose (CO3):** Orchestrates 3 isolated containers (`aegis_web_api`, `aegis_watchdog_worker`, and `aegis_redis`).
- **Automated CI/CD Pipeline (CO2):** GitHub Actions workflow automatically runs `pytest` security tests and verifies Docker image builds on every push and Pull Request.
- **Dual-Persona UX Dashboard (CO4):** Split interface designed for Vault Owners (heartbeat check-ins) and Beneficiaries (emergency decryption).

## 🛠️ Quick Start (Docker Compose)
```bash
docker compose up --build -d