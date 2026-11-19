# parasol.network

Collection maintained by **Parasol Network Engineering**.

Provides configuration backup and light circuit-health checks for devices
managed through the Network inventory and portal job templates.

## Roles

| Role | Purpose |
|------|---------|
| `parasol.network.backup_device_config` | Pull running-config and store under a dated path |
| `parasol.network.circuit_health` | Sanity-check interface operational status |
