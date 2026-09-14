# Red Hat Ansible Automation Platform Self-Service Portal Collection

Ansible collection for deploying AAP Self-Service Portal on OpenShift.

## Description

This collection provides automation to deploy and configure the Red Hat Ansible Automation Platform (AAP) Self-Service Portal on OpenShift clusters. It includes roles for setting up OAuth2 integration, deploying the portal via Helm, and configuring dynamic plugins.

Tested with:
- Ansible Automation Platform 2.6
- Self-Service Automation Portal (GA with AAP 2.6)
- OpenShift 4.18+

## Collection Contents

### Roles

- **self-service**: Main role for deploying AAP Self-Service Portal
  - Creates OAuth2 application in AAP
  - Generates AAP access tokens
  - Creates OpenShift namespace and secrets
  - Builds and deploys plugin registry
  - Deploys AAP Self-Service Portal via Helm
  - Updates OAuth2 redirect URIs

## Installation

```bash
ansible-galaxy collection install rhpds.aap_self_service_portal
```

Or install from source:

```bash
git clone https://github.com/rhpds/rhpds.aap_self_service_portal.git
cd rhpds.aap_self_service_portal
ansible-galaxy collection build
ansible-galaxy collection install rhpds-aap_self_service_portal-*.tar.gz
```

## Requirements

- OpenShift cluster access
- AAP 2.6+ instance running on OpenShift
- Ansible collections:
  - `redhat.openshift`
  - `kubernetes.core`
  - `ansible.controller`

## Usage

### Basic Example

```yaml
- name: Deploy AAP Self-Service Portal
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Include self-service role
      ansible.builtin.include_role:
        name: rhpds.aap_self_service_portal.self_service
      vars:
        controller_host: "https://aap-controller.apps.example.com"
        controller_username: admin
        controller_password: "{{ aap_admin_password }}"
        openshift_namespace: ssap
        openshift_base_domain: "apps.example.com"
```

### AgnosticD v2 Integration

```yaml
workloads:
  - rhpds.aap_self_service_portal.self_service

# Variables
controller_host: "{{ aap_controller_url }}"
controller_username: "{{ aap_admin_username }}"
controller_password: "{{ aap_admin_password }}"
openshift_namespace: "{{ aap_namespace }}-ssap"
```

## Variables

Key variables (see `roles/self-service/defaults/main.yml` for full list):

| Variable | Description | Default |
|----------|-------------|---------|
| `controller_host` | AAP Controller URL | Required |
| `controller_username` | AAP admin username | Required |
| `controller_password` | AAP admin password | Required |
| `openshift_namespace` | OpenShift namespace for portal | `ssap` |
| `openshift_base_domain` | Cluster base domain | Auto-detected |
| `helm_chart_version` | Portal Helm chart version | `2.2.4` |
| `aap_ssl_verify` | Verify AAP SSL certificates | `false` |

## OpenShift Base Domain Detection

The role automatically detects the OpenShift base domain using multiple methods:

1. **IngressController** (requires cluster-admin): Queries `openshift-ingress-operator/default`
2. **Console Route** (fallback): Extracts domain from `openshift-console/console` route
3. **Manual override**: Pass `openshift_base_domain` variable

This allows the role to work with both cluster-admin and regular user permissions.

**This fix resolves the error:**
```
Error from server (Forbidden): ingresscontrollers.operator.openshift.io "default" is forbidden:
User "user1" cannot get resource "ingresscontrollers"
```

## License

MIT

## Author Information

- Hicham Mourad <hmourad@redhat.com>
- Prakhar Srivastava <psrivast@redhat.com>

Red Hat Demo Platform (RHDP)
