# Managed Tenants CLI

A CLI tool commonly used by MT-SRE projects at Red Hat.

## Usage

### Available subcommands

| Subcommand       | Description                                                                        |
|------------------|------------------------------------------------------------------------------------|
| `load`           | Loads the addons inventory                                                         |
| `run`            | Runs the task                                                                      |
| `task_reference` | [path:search] "path" for the directory or file and "search" string to filter tasks |

### Available flags

| Flag                 | Description                            |
|----------------------|----------------------------------------|
| `-v` or `--version`  | CLI version                            |
| `--environment`      | Target environment                     |
| `--adon-name`        | Load only a given addon                |
| `--addon-dir`        | [path] "path" for the addons directory |
| `--ocm-api`          | Override the environments in OCM API   |
| `--ocm-api-insecure` | Allow Insecure connections to OCM API  |

## Install

From PyPI:
```bash
$ pip install managedtenants_cli
```

From source:
```bash
$ python setup.py install
```

## Develop

Install the development requirements:

```bash
$ make develop
```

Run the code checks and tests:
```bash
$ make check
```


## Release

Edit the VERSION file and change the new version. Submit a pull request to master. When it is merged, create a tag and push it to app-sre/sretoolbox.

This will trigger a CI job that will publish the package on pypi.

## License

The default license of the code in this repository is [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0). That applies for most of the code here, as they were written from scratch, but exceptions exist. In any case, each module carries the corresponding licensing information.
