# EventumCLI
Command line interface for Eventum

## Overview
Eventum CLI provides command line interface to run instances of generator.

## Installation

Using PipX (recommended):
```bash
pipx install eventum-cli
```

Using Pip:
```bash
pip install eventum-cli
```

## Usage

To run single instance:
```bash
eventum -t <time mode> -c <config file> [-p <parameters> -s <settings> -v]
```

To run multiple instances using compose file:
```bash
eventum-compose -c <compose config file>
```

See more about configuring and running Eventum here: https://eventum-generatives.github.io/Website/docs/configuring/config_file/
