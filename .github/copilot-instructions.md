# Quod Libet Copilot Instructions

Quod Libet is a Python audio library manager and player built with GTK, with a plugin-based architecture.

The `music-server-main` branch is personal and will never be merged into `main`.

## Development guidance

- Follow existing code patterns and keep changes focused. Separate functions and classes with two blank lines.
- Preserve backward compatibility, lazy imports, and delayed GTK imports in CLI entry points. Handle optional dependencies gracefully.
- Use `quodlibet.util.dprint` for debug, error, and warning output.
- Use Quod Libet's gettext helpers for user-facing strings.
- When changing core behavior, consider its effects on related areas such as browsers, plugins, configuration, and playback.
- Run the relevant tests with the project's pytest-based test suite; avoid network-dependent tests when they are not needed.
- Consider platform-specific behavior when touching platform-dependent code.
