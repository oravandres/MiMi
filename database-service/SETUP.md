# Setting Up the MiMi Database Service

This document provides instructions for setting up and running the MiMi Database Service.

## Prerequisites

- Docker and Docker Compose
- Proper permissions to run Docker commands

## Running with Docker

There are two options to run the database service with Docker:

### Option 1: Using sudo (if you don't have Docker permissions)

If you get a "permission denied" error when trying to run Docker commands, you can use sudo:

```bash
# Navigate to the database service directory
cd database-service

# Run the services with sudo
sudo docker compose up -d
```

### Option 2: Add your user to the Docker group

If you want to run Docker without sudo, you need to add your user to the Docker group:

```bash
# Add current user to Docker group
sudo usermod -aG docker $USER

# Apply the new group membership (log out and log back in, or run:)
newgrp docker

# Then run Docker Compose
docker compose up -d
```

## Manual Setup without Docker

If you prefer not to use Docker, you can set up the components manually:

### PostgreSQL Setup

1. Install PostgreSQL:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

2. Start PostgreSQL:
```bash
sudo service postgresql start
```

3. Create a database and user:
```bash
sudo -u postgres psql
```

4. In the PostgreSQL prompt:
```sql
CREATE USER mimi_user WITH PASSWORD 'mimi_password';
CREATE DATABASE mimi_db OWNER mimi_user;
\q
```

5. Run the database initialization script:
```bash
sudo -u postgres psql -d mimi_db -f db/init/01-schema.sql
```

### API Service Setup

1. Navigate to the app directory:
```bash
cd database-service/app
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export DB_USER=mimi_user
export DB_PASSWORD=mimi_password
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=mimi_db
```

4. Run the API service:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Verifying the Installation

After setup, you should be able to access:

- The API at: http://localhost:8000
- API Documentation at: http://localhost:8000/docs
- pgAdmin (if using Docker) at: http://localhost:5050

## Importing Sample Data

To import sample data:

```bash
# If using Docker:
sudo docker compose exec api python import_sample_data.py

# If manual setup:
python import_sample_data.py
```

## Troubleshooting

### Permission Denied for Docker Socket

If you see this error:
```
permission denied while trying to connect to the Docker daemon socket
```

You need to either:
1. Use sudo with Docker commands
2. Add your user to the Docker group as described above

### Database Connection Issues

If the API cannot connect to the database:

1. Check that PostgreSQL is running:
```bash
sudo service postgresql status
```

2. Verify connection details in the environment variables
3. Check PostgreSQL connection permissions in pg_hba.conf 