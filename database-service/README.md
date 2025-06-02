# MiMi Database Service

This service provides a PostgreSQL database and REST API for storing and retrieving data related to MiMi projects, tasks, agents, and generated artifacts.

## Features

- PostgreSQL database with schemas for projects, tasks, agents, artifacts, and logs
- REST API built with FastAPI for database access
- pgAdmin web interface for database administration
- Docker Compose setup for easy deployment
- Sample data import from MiMi YAML files

## Architecture

The service consists of three main components:

1. **PostgreSQL Database**: Stores all data in a normalized relational schema
2. **FastAPI Service**: Provides REST endpoints for CRUD operations
3. **pgAdmin**: Web-based administration tool for the database

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ (optional, for local development)

### Running the Service

1. Clone the repository
2. Navigate to the database-service directory
3. Start the services:

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database on port 5432
- pgAdmin web interface on port 5050
- API service on port 8000

### API Documentation

Once the service is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### pgAdmin Access

Access pgAdmin at http://localhost:5050 with:
- Email: admin@mimi.local
- Password: admin

To connect to the PostgreSQL server:
1. Add a new server
2. Name: MiMi Database
3. Connection:
   - Host: postgres
   - Port: 5432
   - Database: mimi_db
   - Username: mimi_user
   - Password: mimi_password

## Importing Sample Data

To import sample data from MiMi YAML files:

```bash
# Inside the API container
docker-compose exec api python import_sample_data.py

# Or with a specific YAML file
docker-compose exec api python import_sample_data.py /path/to/project.yaml
```

## Database Schema

The database consists of the following main tables:

- **projects**: Project metadata and configuration
- **tasks**: Individual tasks within projects
- **task_dependencies**: Dependencies between tasks
- **agents**: Agent definitions with model settings
- **artifacts**: Outputs produced by tasks (code, docs, etc.)
- **execution_logs**: Logs of system activity

## API Endpoints

The service provides endpoints for:

- **Projects**: `/projects/`
- **Tasks**: `/tasks/`
- **Task Dependencies**: `/task-dependencies/`
- **Agents**: `/agents/`
- **Artifacts**: `/artifacts/`
- **Execution Logs**: `/logs/`

## Environment Variables

The service can be configured with the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| DB_USER | mimi_user | Database username |
| DB_PASSWORD | mimi_password | Database password |
| DB_HOST | postgres | Database hostname |
| DB_PORT | 5432 | Database port |
| DB_NAME | mimi_db | Database name |

## Development

To run the service locally for development:

1. Install requirements:
```bash
cd app
pip install -r requirements.txt
```

2. Run the FastAPI service:
```bash
uvicorn main:app --reload
```

## Extending the Service

To add new entity types or endpoints:

1. Add the model to `models.py`
2. Create Pydantic schemas in `schemas.py`
3. Add CRUD operations in `crud.py`
4. Register API endpoints in `main.py` 