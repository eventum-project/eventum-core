# EventumPlugins
Plugins for Eventum

## Overview
Package includes next types of plugins for Eventum:
1. Input plugins
2. Event plugins
3. Output plugins

Current list of implemented plugins and their description: https://eventum-generatives.github.io/Website/docs/plugins/

## Installation
```bash
pip install eventum-plugins
```

## Developing
When developing new plugins you should follow next clauses:
1. Plugin is a separate module within a package
2. Plugin class should inherit base class
3. Each plugin should define its configuration class that inherits base config class 
4. Plugin module should contain defined `PLUGIN_CLASS` and `CONFIG_CLASS` variables (it automatically marks plugins as plugable)

If you want your plugin to be merged, please:
- write and provide documentation for your plugin by making PR to https://github.com/Eventum-Generatives/Website
- write tests for your plugin
