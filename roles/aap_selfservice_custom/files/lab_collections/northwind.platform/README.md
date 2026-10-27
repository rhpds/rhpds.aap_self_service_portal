# northwind.platform

Internal Ansible collection owned by **Northwind Platform Engineering**.

Used across Controller job templates and the Self-Service Automation Portal to
apply a consistent Linux host baseline and to enforce change-window policy
before disruptive automation runs.

## Roles

| Role | Purpose |
|------|---------|
| `northwind.platform.host_baseline` | MOTD, timezone, chrony presence, admin SSH banner |
| `northwind.platform.change_window` | Fail the play when outside approved maintenance windows |

## Example

```yaml
- hosts: rhel
  become: true
  roles:
    - role: northwind.platform.change_window
      vars:
        northwind_change_window_tz: America/New_York
        northwind_change_window_days: [6, 0]   # Sat/Sun
        northwind_change_window_start_hour: 2
        northwind_change_window_end_hour: 6
    - role: northwind.platform.host_baseline
      vars:
        northwind_motd_environment: production
```

## Support

Platform Automation — `#nw-platform-automation` · platform-automation@northwind.example
