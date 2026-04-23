# Grafana Documentation for IoTDash

This directory contains comprehensive documentation for managing Grafana dashboards in the IoTDash platform.

## Documents

### 📘 [User Guide](./USER_GUIDE.md)
**Audience**: End users, dashboard viewers, organization admins

Learn how to:
- Navigate and customize Grafana dashboards
- Add new panels and visualizations
- Understand data lifecycle and retention
- Manage growing metrics and optimize queries
- Troubleshoot common issues

**Recommended for**:
- New users onboarding to IoTDash
- Users wanting to customize their dashboards
- Anyone needing to understand how data flows through the system

---

### 🔧 [Provisioning Guide](./PROVISIONING_GUIDE.md)
**Audience**: System administrators, DevOps engineers, developers

Technical deep-dive into:
- Dashboard provisioning architecture
- How organizations are automatically provisioned with Grafana dashboards
- Template management and updates
- Proposed improvements and roadmap
- Implementation guides for advanced features

**Recommended for**:
- Admins managing IoTDash deployments
- Developers contributing to the platform
- Anyone responsible for dashboard template maintenance

---

### 🎓 [Workshop Outline](./WORKSHOP_OUTLINE.md)
**Audience**: Workshop facilitators, training teams

Complete 2-3 hour training program including:
- Detailed session plans with timing
- Hands-on lab exercises with solutions
- Presentation slides content
- Q&A and best practices
- Post-workshop materials and follow-up

**Recommended for**:
- Training teams onboarding new users
- Organizations rolling out IoTDash to multiple teams
- Anyone planning Grafana training sessions

---

## Quick Start

### For End Users

1. **Start here**: Read the [User Guide](./USER_GUIDE.md) sections 1-3 for basics
2. **Hands-on**: Follow a hands-on lab from the [Workshop](./WORKSHOP_OUTLINE.md) (Session 2 or 3)
3. **Advanced**: Explore query optimization in [User Guide](./USER_GUIDE.md) section 7

### For Administrators

1. **Architecture**: Read [Provisioning Guide](./PROVISIONING_GUIDE.md) sections 1-2
2. **Current process**: Understand [Provisioning Guide](./PROVISIONING_GUIDE.md) section 4
3. **Improvements**: Review [Provisioning Guide](./PROVISIONING_GUIDE.md) section 7

### For Trainers

1. **Review materials**: Read all three documents
2. **Customize**: Adapt [Workshop Outline](./WORKSHOP_OUTLINE.md) to your audience
3. **Prepare**: Use workshop prep checklist in appendix
4. **Deliver**: Follow session timing and lab exercises

---

## Document Status

| Document | Version | Last Updated | Status |
|----------|---------|--------------|--------|
| User Guide | 1.0 | April 2026 | ✅ Complete |
| Provisioning Guide | 1.0 | April 2026 | ✅ Complete |
| Workshop Outline | 1.0 | April 2026 | ✅ Complete |

---

## Contributing

### Updating Documentation

If you find errors or have improvements:

1. **Minor fixes** (typos, broken links):
   - Edit the markdown file directly
   - Submit a pull request

2. **Major changes** (new sections, restructuring):
   - Open an issue first to discuss
   - Get feedback from maintainers
   - Submit PR with changes

### Documentation Standards

- Use clear, concise language
- Include code examples where relevant
- Add screenshots for UI-heavy sections (future enhancement)
- Test all commands and queries before documenting
- Update version and last updated date

### Versioning

Documents follow semantic versioning:
- **Major** (1.0 → 2.0): Significant restructuring or new IoTDash version
- **Minor** (1.0 → 1.1): New sections or substantial additions
- **Patch** (1.0.0 → 1.0.1): Fixes, typos, clarifications

---

## Related Resources

### External Documentation
- [Grafana Official Docs](https://grafana.com/docs/)
- [InfluxDB Query Language](https://docs.influxdata.com/influxdb/v1.8/query_language/)
- [MQTT Protocol Specification](https://mqtt.org/mqtt-specification/)

### IoTDash Documentation
- [Main README](../../README.md) - Project overview
- [Backend API Docs](../../backend/README.md) - API reference (if exists)
- [Frontend Guide](../../frontend/README.md) - UI development (if exists)

### Code References
- Dashboard provisioning: [`backend/app/routers/admin_orgs.py`](../../backend/app/routers/admin_orgs.py)
- Grafana API client: [`backend/app/services/grafana_client.py`](../../backend/app/services/grafana_client.py)
- Dashboard template: [`grafana/provisioning/dashboards/iot-metrics.json`](../../grafana/provisioning/dashboards/iot-metrics.json)

---

## Feedback

Have questions or suggestions about this documentation?

- **File an issue**: [GitHub Issues](https://github.com/svolodarskyi/iotdash/issues)
- **Contact**: [Your support email]
- **Contribute**: Submit a pull request

---

## License

Documentation is licensed under [Your License] - same as IoTDash project.

---

**Maintained by**: IoTDash Team
**Last Review**: April 2026
**Next Review**: July 2026
