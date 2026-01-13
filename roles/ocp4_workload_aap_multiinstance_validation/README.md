# AAP Multi-Instance Workshop Validation Role

Comprehensive validation role for the AAP Multi-Instance Workshop environment. Runs AFTER all workloads complete to verify workshop component health.

## Overview

This role validates all deployed components in a multi-user AAP workshop environment (1-60 users), checking:

### Shared Components
- **Keycloak**: Operator CSV, instance CR, pods, route accessibility

### Per-User Components (for EACH user)
- **AAP Operator**: CSV status, operator pods (in each user's AAP namespace)
- **AAP Instance**: AutomationController CR, EDA CR, pods (controller, EDA, PostgreSQL, Redis), routes (gateway & controller)
- **Self-Service Portal**: Deployment, pods, route accessibility
- **Showroom**: Deployment, pods, route accessibility (namespace: showroom-{guid}-userN)

## Features

- Individual component validation with granular status tracking
- HTTP accessibility checks for all user-facing routes
- Comprehensive health report with three status levels:
  - **HEALTHY**: All checks pass, routes accessible
  - **DEGRADED**: Partial issues (pods not ready, HTTP not accessible)
  - **FAILED**: Critical issues (missing resources, pods not running)
- Results displayed in catalog info page via `agnosticd_user_info`
- Toggleable validation checks for flexibility

## AgnosticV Integration

### Catalog Parameter

Users can optionally enable validation during deployment:

```yaml
parameters:
  - name: enable_aap_workshop_validation
    formLabel: Enable Workshop Environment Validation
    description: Run validation checks after deployment to verify all components are healthy
    openAPIV3Schema:
      type: boolean
      default: false
```

### Workload Configuration

In `common.yaml`:

```yaml
# Enable/disable workshop environment validation
enable_aap_workshop_validation: false

workloads:
  - agnosticd.core_workloads.ocp4_workload_authentication_keycloak
  - rhpds.aap_self_service_portal.ocp4_workload_aap_multiinstance
  - rhpds.aap_self_service_portal.self_service
  - rhpds.aap_self_service_portal.aap_selfservice_custom
  - agnosticd.showroom.ocp4_workload_showroom_ocp_integration
  - agnosticd.showroom.ocp4_workload_showroom
  - "{{ 'rhpds.aap_self_service_portal.ocp4_workload_aap_multiinstance_validation' if enable_aap_workshop_validation | bool else omit }}"
```

### Info Page Display

Validation results appear in `info-message-template.adoc`:

```asciidoc
ifdef::validation_status[]

== Workshop Environment Validation Report

[%autowidth.stretch,width=80%,cols="a,a",options="header"]
|===
2+| Environment Health Check
| Overall Status | *{validation_status}*
| Total Components | {validation_total}
| Healthy | {validation_healthy}
| Degraded | {validation_degraded}
| Failed | {validation_failed}
2+| *Issues Detected*
2+| {validation_issues}
|===

endif::[]
```

## Default Variables

All variables prefixed with `ocp4_workload_aap_multiinstance_validation_`

### Multi-User Configuration

```yaml
ocp4_workload_aap_multiinstance_validation_num_users: "{{ num_users | default(1) | int }}"
ocp4_workload_aap_multiinstance_validation_user_prefix: "user"
```

### Component Toggles

```yaml
ocp4_workload_aap_multiinstance_validation_check_keycloak: true
ocp4_workload_aap_multiinstance_validation_check_aap_operator: true
ocp4_workload_aap_multiinstance_validation_check_aap_instances: true
ocp4_workload_aap_multiinstance_validation_check_self_service_portals: true
ocp4_workload_aap_multiinstance_validation_check_showroom: true
```

### Namespace Configuration

```yaml
ocp4_workload_aap_multiinstance_validation_keycloak_namespace: keycloak
ocp4_workload_aap_multiinstance_validation_aap_namespace_suffix: "-aap"  # AAP operator and instance namespace suffix
ocp4_workload_aap_multiinstance_validation_ssap_namespace_suffix: "-aap-ssap"
ocp4_workload_aap_multiinstance_validation_showroom_namespace: showroom-{{ guid | default('00000') }}  # Base pattern, -userN added per-user
```

### HTTP Check Settings

```yaml
ocp4_workload_aap_multiinstance_validation_http_timeout: 30
ocp4_workload_aap_multiinstance_validation_http_validate_certs: false
ocp4_workload_aap_multiinstance_validation_http_success_codes:
  - 200
  - 301
  - 302
  - 303
  - 307
```

## Task Files

### Main Orchestration

- `tasks/main.yml`: Entry point, initializes variables and calls component checks

### Component Checks

- `tasks/check_keycloak.yml`: Validates Keycloak operator and instance
- `tasks/check_aap_operator.yml`: Loops through all users to validate AAP operators
- `tasks/check_single_aap_operator.yml`: Validates one user's AAP operator
- `tasks/check_aap_instances.yml`: Loops through all users to validate AAP instances
- `tasks/check_single_aap_instance.yml`: Validates one user's AAP deployment
- `tasks/check_self_service_portals.yml`: Loops through all users to validate portals
- `tasks/check_single_ssap.yml`: Validates one user's self-service portal
- `tasks/check_showroom_instances.yml`: Loops through all users to validate Showroom instances
- `tasks/check_single_showroom.yml`: Validates one user's Showroom deployment

### Report Generation

- `tasks/generate_report.yml`: Compiles results, saves to `agnosticd_user_info`

## Validation Logic

### Per-User AAP Operator

For each user:

1. **Namespace**: `{user}-aap` (e.g., user1-aap)
2. **Operator CSV**: Status phase = Succeeded
3. **Operator pods**: All Running

### Per-User AAP Instance

For each user (user1, user2, ..., user60):

1. **Namespace**: `{user}-aap` (e.g., user1-aap)
2. **AutomationController CR**: Status condition "Running" = True
3. **EDA CR**: Status condition "Running" = True (if enabled)
4. **Controller pods**: All Running with ready containers
5. **EDA pods**: All Running with ready containers
6. **PostgreSQL pods**: All Running
7. **Redis pods**: All Running
8. **AAP Gateway route**: Exists and HTTP accessible at `/api/gateway/v1/`
9. **AAP Controller route**: Exists

### Per-User Self-Service Portal

For each user:

1. **Namespace**: `{user}-aap-ssap` (e.g., user1-aap-ssap)
2. **Deployment**: Available condition = True
3. **Pods**: All Running with ready containers
4. **Route**: Exists and HTTP accessible

### Per-User Showroom

For each user:

1. **Namespace**: `showroom-{guid}-user{N}` (e.g., showroom-5l9zg-user1)
2. **Deployment**: Available condition = True
3. **Pods**: All Running with ready containers
4. **Route**: Exists and HTTP accessible

### Status Determination

**FAILED** if:
- CR status not Ready/Running
- Zero pods running
- No route exists

**DEGRADED** if:
- Some pods not ready
- Route exists but HTTP check fails
- Replicas not matching desired count

**HEALTHY** if:
- All CRs ready
- All pods running and ready
- Routes accessible via HTTP

## User Info Data

Saved via `agnosticd_user_info` for catalog display:

```yaml
validation_status: "HEALTHY" | "DEGRADED" | "FAILED"
validation_total: "123"
validation_healthy: "120"
validation_degraded: "3"
validation_failed: "0"
validation_issues: "user45: Gateway route not HTTP accessible, user23 SSAP: 1/1 pods running"
validation_summary: "<full text report with component details>"
```

## Error Handling

- Uses `ignore_errors: true` on all `k8s_info` tasks
- Gracefully handles missing resources (sets status to "NotFound")
- Non-blocking - validation failures don't fail the deployment
- HTTP checks timeout after 30 seconds

## Example Output

```
AAP Multi-Instance Workshop Validation Report
================================================

Overall Status: DEGRADED
Timestamp: 2026-01-13T15:30:45Z

Components Summary:
- Total: 123
- Healthy: 120
- Degraded: 3
- Failed: 0

Issues Detected:
- user45: Gateway route not HTTP accessible
- user23 SSAP: deployment not available
- user38: EDA not ready

Component Details:

Keycloak (keycloak):
  Status: HEALTHY
  operator_csv: Succeeded
  operator_pods: 1/1
  instance_ready: True
  pods: 1/1
  route: https://keycloak-keycloak.apps.cluster.com
  http_accessible: True

AAP Instance - user1 (user1-aap):
  Status: HEALTHY
  controller_ready: True
  controller_pods: 4/4
  eda_ready: True
  eda_pods: 2/2
  postgres_pods: 1/1
  redis_pods: 1/1
  gateway_route: https://user1-aap-user1-aap.apps.cluster.com
  controller_route: https://user1-aap-controller-user1-aap.apps.cluster.com
  http_accessible: True

[... continues for all users ...]
```

## Customization

### Disable Specific Component Checks

Override in AgnosticV `common.yaml`:

```yaml
ocp4_workload_aap_multiinstance_validation_check_showroom: false
ocp4_workload_aap_multiinstance_validation_check_eda: false
```

### Adjust HTTP Timeout

```yaml
ocp4_workload_aap_multiinstance_validation_http_timeout: 60
```

### Custom Namespace Patterns

```yaml
ocp4_workload_aap_multiinstance_validation_user_prefix: "student"
ocp4_workload_aap_multiinstance_validation_aap_namespace_suffix: "-ansible"
```

## Dependencies

- `kubernetes.core` collection
- `agnosticd.core` collection (for `agnosticd_user_info`)
- OpenShift cluster with admin access
- AAP 2.6+ (Platform Gateway architecture)

## Author

Prakhar Srivastava <psrivast@redhat.com>
Manager, Technical Marketing – Red Hat Demo Platform (RHDP)

## License

MIT
