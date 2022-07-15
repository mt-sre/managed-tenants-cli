# Managed Tenants CLI

A CLI tool commonly used by MT-SRE projects at Red Hat.

## Usage

### Available subcommands

| Subcommand       | Description                                                                        |
| ---------------- | ---------------------------------------------------------------------------------- |
| `load`           | Loads the addons inventory                                                         |
| `run`            | Runs the task                                                                      |
| `tasks_reference` | [path:search] "path" for the directory or file and "search" string to filter tasks |

### Available flags

| Flag                 | Description                            |
| -------------------- | -------------------------------------- |
| `-v` or `--version`  | CLI version                            |
| `--environment`      | Target environment                     |
| `--addon-name`        | Load only a given addon                |
| `--addons-dir`        | [path] "path" for the addons directory |
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

Install `pre-commit` hooks:
```bash
$ pre-commit install
```

Install the development requirements:

```bash
$ make develop
```

Run the code checks:

```bash
$ make check
```

Run the tests:

```bash
$ make test
```

## Release

Update the VERSION file and change the new version. Submit a pull request and merge it to main. Once it is merged, you need to create a new tag and a new release. You can do this by clicking "Draft a new release" on the release page and then creating a new tag instead of selecting one from the dropdown. Please also use the option to "Generate release notes". After that, a CI job will be triggered that will publish the package on PyPI.


Alternatively, you can create a new tag by running:
```
git checkout main && git pull upstream main
git tag X.Y.Z
git push upstream X.Y.Z
```
and then draft the release in the web UI. 

## License

The default license of the code in this repository is [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0). That applies for most of the code here, as they were written from scratch, but exceptions exist. In any case, each module carries the corresponding licensing information.
