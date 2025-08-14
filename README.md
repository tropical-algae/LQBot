# LQBot

None

## Development Requirements

- Ubuntu 20.04 / 22.04
- Python 3.10.14
- Pip
- Poetry (Python Package Manager)
- Make

## How to start?

Install poetry, download dependencies, and activate the poetry development environment through the following commands. We will create the virtual environment required for development under the project by default.

```sh
make install
```

To start from the terminal again, you need to activate the environment first:

```sh
make activate
```

### Configure your `.env`

Before starting the project, please complete the configuration first.

[.env.example](.env.example) is a sample configuration, for more configurations, please check [HERE](src/lqbot/common/config.py)

### Runnning

Start your system with the following command:

```sh
poe run
```

### Testing

The `check` command only performs static checks on the code, including syntax and import checks. The `test` command will perform unit testing. Alternatively, you can choose `check-test` to run them together

```sh
poe check
poe test
poe check-test
```

### Cleaning Cache

```sh
poe clean
```

### Database visioning

When the database schema changes, create a new version promptly. This is an auto function for SQL table build.

```sh
alembic upgrade head
alembic revision --autogenerate -m ""
```

OR, if you already has a SQL table, you could auto-build sqlmodel BaseModel code by this:

Add the target table you want to build code in Makefile before you run this.

```sh
poe update-db
```

## Access Swagger Documentation

> <http://localhost:8080/docs>

The system defaults to starting on port `8000`, or you can modify this value in the configuration file
