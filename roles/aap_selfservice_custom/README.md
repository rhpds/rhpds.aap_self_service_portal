# AAP Self-Service Custom Content Role

Configures Ansible Automation Platform instances with demo users, inventories, credentials, projects, and job templates for self-service portal demonstrations.

## Description

This role populates AAP instances with pre-configured demo content to showcase the self-service automation portal. It supports both single-instance and multi-user deployments, automatically detecting the deployment mode via the `agnosticd_user_data` lookup plugin.

## Maintainer

**Hicham Mourad** <hmourad@redhat.com>

This role is designed to be independently customizable by the maintainer.

## Requirements

- Ansible Automation Platform 2.5+
- `ansible.controller` collection (>= 4.5.0)
- AAP instances deployed via `rhpds.aap_self_service_portal.ocp4_workload_aap_multiinstance`

## Role Variables

### Connection Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `aap_selfservice_custom_controller_url` | `""` | AAP controller URL (auto-populated from lookup) |
| `aap_selfservice_custom_admin_username` | `"admin"` | AAP admin username |
| `aap_selfservice_custom_admin_password` | `""` | AAP admin password (auto-populated) |
| `aap_selfservice_custom_organization` | `"Default"` | Default organization name |
| `aap_selfservice_custom_verify_ssl` | `false` | Verify SSL certificates |

### Demo Content

| Variable | Description |
|----------|-------------|
| `aap_selfservice_custom_users` | List of demo users (clouduser1, networkuser1, rheluser1) |
| `aap_selfservice_custom_inventories` | List of demo inventories (AWS, Azure, GCP, RHEL, Network) |
| `aap_selfservice_custom_credentials` | List of demo credentials (placeholder values for CNV) |
| `aap_selfservice_custom_projects` | List of SCM projects (ansible-tmm/ssap-lab) |
| `aap_selfservice_custom_labels` | List of labels (aws, rhel, network, custom) |
| `aap_selfservice_custom_job_templates` | List of 15 job templates (5 AWS + 4 Network + 6 RHEL) |

### Behavior

| Variable | Default | Description |
|----------|---------|-------------|
| `aap_selfservice_custom_user_password` | `common_password` | Password for demo users |
| `aap_selfservice_custom_skip_existing` | `true` | Skip resources that already exist (idempotent) |
| `aap_selfservice_custom_debug` | `false` | Enable debug output |

## Dependencies

- `rhpds.aap_self_service_portal.ocp4_workload_aap_multiinstance` - Must run before this role

## Example Playbook

### Single Instance

```yaml
- name: Configure AAP with demo content
  hosts: localhost
  roles:
    - role: rhpds.aap_self_service_portal.aap_selfservice_custom
```

### Multi-User (Automatic Detection)

```yaml
workloads:
  - rhpds.aap_self_service_portal.ocp4_workload_aap_multiinstance
  - rhpds.aap_self_service_portal.self_service
  - rhpds.aap_self_service_portal.aap_selfservice_custom  # Runs against all instances
```

## Demo Content Details

### Users (3)
- **clouduser1** - Cloud automation demos
- **networkuser1** - Network automation demos
- **rheluser1** - RHEL automation demos

All users use the workshop `common_password`.

### Inventories (5)
- AWS Inventory
- Azure Inventory
- GCP Inventory
- RHEL Inventory
- Network Inventory

### Credentials (5)
- **AWS Credentials** - Placeholder AWS access keys
- **Azure Credentials** - Placeholder Azure subscription ID
- **RHEL - SSH Credentials** - Machine credentials for RHEL
- **Network Credentials** - Machine credentials for network devices

**Note:** Credentials use placeholder values suitable for CNV/demo environments. Update for production use.

### Project (1)
- **SelfService Demo playbooks** - Git project from https://github.com/ansible-tmm/ssap-lab

### Labels (4)
- `aws` - AWS-related templates
- `rhel` - RHEL-related templates
- `network` - Network-related templates
- `custom` - Custom templates for portal import

### Job Templates (15)

#### AWS Templates (5)
1. Cloud/AWS AWS Provisioning Workflow
2. Cloud/AWS Create RHEL10 instance
3. Cloud/AWS Create RHEL9 instance
4. Cloud/AWS Create VPC
5. Cloud/AWS Snapshot ec2 instance

#### Network Templates (4)
6. Network/Backup Network Device
7. Network/Deploy Network device configuration
8. Network/Onboard Network device
9. Network/Restore Network device

#### RHEL Templates (6)
10. Linux/RHEL Deploy Applications to RHEL
11. Linux/RHEL Install NGINX on RHEL
12. Linux/RHEL Patch RHEL Servers
13. Linux/RHEL START Service on RHEL
14. Linux/RHEL STOP Service on RHEL
15. RHEL / Update RHEL Time Servers *(custom - for portal import)*

## How It Works

1. **Detection**: Checks `agnosticd_user_data` for `aap_multi_user_mode`
2. **Single Mode**: Configures one AAP instance
3. **Multi-User Mode**: Loops through all AAP instances from `aap_instances` list
4. **Per Instance**:
   - Tests AAP API connectivity
   - Creates users → inventories → credentials → labels → projects
   - Waits for project SCM sync
   - Creates job templates

## Customization

To customize demo content:

1. **Update variables** in `defaults/main.yml`:
   - Add/remove users, inventories, credentials
   - Modify job templates, playbooks, labels

2. **Change source project**:
   ```yaml
   aap_selfservice_custom_projects:
     - name: My Custom Project
       scm_url: https://github.com/my-org/my-playbooks
   ```

3. **Override in AgnosticV**:
   ```yaml
   aap_selfservice_custom_users:
     - username: myuser1
       password: "{{ common_password }}"
       email: myuser1@example.com
       first_name: My
       last_name: User
   ```

## CNV Environment Notes

This role is designed for **CNV/demo environments** where cloud provider credentials are placeholders for UI demonstration only. The job templates will appear in AAP and the self-service portal but will not execute against real cloud infrastructure.

For production environments with real cloud providers, update the credentials configuration with proper secrets management.

## Troubleshooting

### Role skipped - no AAP instances found
- Ensure `ocp4_workload_aap_multiinstance` ran successfully first
- Check that `agnosticd_user_info` data was saved

### Credential creation fails
- Verify credential types exist in AAP (Amazon Web Services, Microsoft Azure Resource Manager, Machine)
- Check organization name matches

### Job template creation fails
- Ensure project SCM sync completed (role includes 30s wait)
- Verify playbook names exist in the SCM repository
- Check that inventory and credential names match exactly

## License

MIT-0

## Author

Prakhar Srivastava <psrivast@redhat.com>
Maintainer: Hicham Mourad <hmourad@redhat.com>

## Source

Based on playbook: https://github.com/ansible-tmm/ssap-lab/blob/main/playbooks/aap-setup.yml
