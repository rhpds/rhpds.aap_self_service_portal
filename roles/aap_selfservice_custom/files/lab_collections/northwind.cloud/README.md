# northwind.cloud

Collection maintained by **Northwind Cloud Operations**.

Enforces tagging policy and lightweight cost-hygiene checks on workloads
provisioned through the Self-Service Automation Portal (AWS / Azure catalogs).

## Roles

| Role | Purpose |
|------|---------|
| `northwind.cloud.instance_tagging` | Ensure required Northwind tags on targeted instances |
| `northwind.cloud.cost_hygiene` | Report instances missing owner/cost-center tags |

## Required tags

- `nw:owner`
- `nw:cost-center`
- `nw:environment`
- `nw:application`
