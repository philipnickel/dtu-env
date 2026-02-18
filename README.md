# dtu-env

DTU course environment manager. Interactive TUI to browse and install conda environments for DTU courses.

## Usage

```bash
dtu-env
```

This launches an interactive terminal interface where you can:

1. See your currently installed conda environments
2. Browse available DTU course environments (fetched from GitHub)
3. Filter/search by course number, name, or semester
4. Multi-select environments and install them

## Install

```bash
pip install dtu-env
```

Or with conda (once available on conda-forge):

```bash
conda install dtu-env
```

## How it works

Course environment definitions (YAML files) are maintained in the
[dtudk/pythonsupport-page](https://github.com/dtudk/pythonsupport-page) repository.
`dtu-env` fetches these at runtime and uses `mamba`/`conda` to create the environments.
