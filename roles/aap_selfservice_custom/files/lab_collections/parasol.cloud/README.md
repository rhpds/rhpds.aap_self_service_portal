# parasol.cloud

Collection maintained by **Parasol Cloud Operations**.

Enforces tagging policy and lightweight cost-hygiene checks on workloads
provisioned through the Self-Service Automation Portal (AWS / Azure catalogs).

## Roles

| Role | Purpose |
|------|---------|
| `parasol.cloud.instance_tagging` | Ensure required Parasol tags on targeted instances |
| `parasol.cloud.cost_hygiene` | Report instances missing owner/cost-center tags |

## Required tags

- `parasol:owner`
- `nw:cost-center`
- `nw:environment`
- `nw:application`
