# Quod Libet Copilot Instructions (command:workbench.action.chat.generateinstructions)

## Project Overview
Quod Libet is a cross-platform GTK+ audio library manager and player written in Python. It features a plugin-based architecture with over 90 included plugins, comprehensive metadata editing, and flexible browsing capabilities.

Git branch 'music-server-main' is a personal branch that will never be merged into 'main'.  

## Architecture & Components

### Core Application Structure
- **`quodlibet/main.py`**: Entry point that initializes library, player, and browsers
- **`quodlibet/app.py`**: Global application state and coordination
- **`quodlibet/config.py`**: Configuration management with `INITIAL` dict defining defaults
- **`quodlibet/_init.py`**: Early initialization including CLI setup

### Key Subsystems
- **Browsers** (`quodlibet/browsers/`): Pluggable UI components for music navigation
  - Follow `_base.py` Filter interface: `can_filter_*()`, `filter()`, `unfilter()`
  - Must define `keys`, `priority` class attributes and implement Browser base class
  - Examples: PanedBrowser, AlbumBrowser, CollectionBrowser
- **Players** (`quodlibet/player/`): Audio backend abstraction
  - Primary: GStreamer (`gstbe/`), Fallback: null (`nullbe.py`)
  - Backend selection via `QUODLIBET_BACKEND` env var or config
- **Plugins** (`quodlibet/ext/`): Categorized by type (events, editing, covers, etc.)
  - Plugin discovery via `quodlibet/plugins/__init__.py` ModuleScanner
  - Use `PluginNotSupportedError` to hide platform-specific plugins

### Library Management
- **Songs storage**: `~/.local/share/quodlibet/songs` (configurable)
- **Config file**: `~/.config/quodlibet/config`
- **Library initialization**: `quodlibet.library.init(library_path)` in main.py

## Development Workflow

### Build System (Custom gdist)
The project uses a custom distutils extension in `gdist/` package:

**Essential Commands:**
```bash
# Run tests
python setup.py test [--suite=tests] [--exitfirst] [--no-network]

# Build documentation  
python setup.py build_sphinx [--all]

# Translation management
python setup.py create_pot       # Create translation template
python setup.py update_po --lang=LANG  # Update translation
python setup.py po_stats --lang=LANG   # Translation statistics

# Quality checks
python setup.py quality          # Code quality checks
python setup.py distcheck        # Full distribution test

# Coverage analysis
python setup.py coverage [--to-run=module]

# Clean build artifacts
python setup.py clean --all
```

### Testing
- **Framework**: pytest with custom `conftest.py` hooks
- **Location**: `tests/` directory
- **Test execution**: Captures uncaught exceptions from PyGObject signal handlers
- **Flaky tests**: Use `@flaky` decorator for unreliable tests
- **Network tests**: Skip with `--no-network` flag

## Code Patterns & Conventions

### Configuration Access
```python
from quodlibet import config
# Get with default fallback from INITIAL dict
value = config.get("section", "key")  
config.set("section", "key", value)
```

### Plugin Development
```python
# Plugin base structure
from quodlibet.plugins import PluginImportError, MissingModulePluginError

class MyPlugin(SomePluginBase):
    PLUGIN_ID = "unique_id"
    PLUGIN_NAME = _("Display Name")
    PLUGIN_DESC = _("Description")
    
    def enabled(self):
        # Plugin activation logic
        
    def disabled(self):
        # Plugin deactivation cleanup
```

### Browser Implementation
```python
class CustomBrowser(Browser):
    keys = ["CustomBrowser"]  # Used for lookup
    priority = 50  # Lower = higher priority
    
    def can_filter_text(self):
        return True  # Enable text search
        
    def filter_text(self, text):
        # Implement filtering logic
```

### Error Handling
- Use `quodlibet.util.dprint.print_d` for debug output
- Use `quodlibet.util.dprint.print_e` for errors  
- Use `quodlibet.util.dprint.print_w` for warnings

### Import Management
- **Lazy imports**: Heavy modules imported on-demand in functions
- **GTK import delay**: `main.py` prevents early GTK imports for CLI performance
- **Module redirect**: `_import.py` provides import hook system

### i18n Support
```python
from quodlibet import _, C_, N_, ngettext
text = _("Translatable text")  # Standard gettext
text = C_("context", "text")   # With context
text = N_("text")              # Mark for translation only
```

## Integration Points

### GStreamer Pipeline
- Default pipeline configurable via `player.gst_pipeline` config
- Custom elements via `quodlibet/player/gstbe/` plugins
- Audio effects via `quodlibet/player/dsp.py`

### D-Bus Integration (Linux)
- MPRIS support for media keys
- Service files in `data/` directory built by gdist

### Cross-Platform Considerations
- **Windows**: DLL loading protection in `__init__.py`
- **macOS**: Special handling via `is_osx` checks
- **Platform detection**: `quodlibet.util.is_windows()`, `is_osx()`

### External Dependencies
- **Required**: mutagen, feedparser, pycairo, pygobject
- **Optional**: musicbrainzngs, dbus-python, soco (plugins)
- **Poetry extras**: Use `poetry install -E plugins` for full feature set

## File Organization Notes
- **Entry scripts**: `quodlibet.py`, `exfalso.py`, `operon.py` in project root
- **Version info**: Defined in `quodlibet/const.py` as `VERSION_TUPLE`
- **Build metadata**: `pyproject.toml` (Poetry) and `setup.py` (gdist) coexist
- **Assets**: Icons in `quodlibet/images/`, data files in `data/`
- **External APIs**: `quodlibet/extapis` for communication with other processes and services

When modifying core functionality, always check impact on browser filtering, plugin loading, and configuration management. The codebase emphasizes backward compatibility and graceful degradation when optional dependencies are missing.