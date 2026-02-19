# dtu-env

DTU course environment manager. Interactive CLI to browse and install conda environments for DTU courses.

## Usage

```bash
dtu-env
```

This launches an interactive terminal where you can:

1. See your currently installed conda environments
2. Browse available DTU course environments (fetched from GitHub)
3. Select one or more environments to install
4. Confirm and install them via mamba/conda

## Install

```bash
pip install dtu-env
```

Or with conda (once available on conda-forge):

```bash
conda install dtu-env
```

## Requirements

- Python >= 3.10
- Miniforge3 (or any conda/mamba installation) on your PATH

## How it works

Course environment definitions (YAML files) are maintained in the
[dtudk/pythonsupport-page](https://github.com/dtudk/pythonsupport-page) repository.
`dtu-env` fetches these at runtime and uses `mamba`/`conda` to create the environments.
