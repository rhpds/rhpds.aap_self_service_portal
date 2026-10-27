# northwind.network

Collection maintained by **Northwind Network Engineering**.

Provides configuration backup and light circuit-health checks for devices
managed through the Network inventory and portal job templates.

## Roles

| Role | Purpose |
|------|---------|
| `northwind.network.backup_device_config` | Pull running-config and store under a dated path |
| `northwind.network.circuit_health` | Sanity-check interface operational status |
