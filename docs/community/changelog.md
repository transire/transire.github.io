---
title: "Changelog"
category: community
subcategory: null
complexity: beginner
duration: null
prerequisites: []
mcp_use: reference
features_covered:
  - Version history
  - Release notes
  - Breaking changes
code_blocks: false
last_updated: 2025-10-31
---

# Changelog

All notable changes to Transire will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial framework implementation
- HTTP handler support with standard Go HTTP patterns
- Queue handler support with type-safe message processing
- Scheduled handler support with cron expressions
- Dependency injection system
- Middleware support
- Local development runtime with in-memory emulation
- Test kit for unit and integration testing
- AWS cloud provider implementation
- OpenTofu-based infrastructure generation
- CLI for manifest generation, local running, and deployment
- GitHub Actions CI/CD workflow generation

### Documentation
- Comprehensive documentation site
- Quickstart guide
- SDK reference documentation
- CLI command reference
- Deployment guides
- Testing guides

## Release Versioning

Transire follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

## Deprecation Policy

When features are deprecated:

1. Deprecation is announced in release notes
2. Feature continues to work for at least one MINOR version
3. Deprecation warnings are added to documentation
4. Migration path is provided
5. Feature is removed in next MAJOR version

## Stay Updated

- Watch the [GitHub repository](https://github.com/transire) for releases
- Subscribe to release notifications
- Follow release notes for upgrade instructions

## Previous Versions

This is the initial release. Version history will be maintained as the project evolves.
