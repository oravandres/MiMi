-- Create schema
CREATE SCHEMA IF NOT EXISTS mimi;

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Projects table
CREATE TABLE IF NOT EXISTS mimi.projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    config JSONB,
    status VARCHAR(50) DEFAULT 'pending'
);

-- Tasks table
CREATE TABLE IF NOT EXISTS mimi.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES mimi.projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    agent VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    input_key JSONB,
    output_key VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    error TEXT,
    duration FLOAT
);

-- Task Dependencies table
CREATE TABLE IF NOT EXISTS mimi.task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES mimi.tasks(id) ON DELETE CASCADE,
    depends_on_task_id UUID NOT NULL REFERENCES mimi.tasks(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_id, depends_on_task_id)
);

-- Agents table
CREATE TABLE IF NOT EXISTS mimi.agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    description TEXT,
    model_name VARCHAR(255) NOT NULL,
    model_provider VARCHAR(255) NOT NULL,
    model_settings JSONB,
    system_prompt TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Artifacts table (for storing code, documentation, etc.)
CREATE TABLE IF NOT EXISTS mimi.artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES mimi.projects(id) ON DELETE CASCADE,
    task_id UUID REFERENCES mimi.tasks(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    path TEXT,
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Execution logs table
CREATE TABLE IF NOT EXISTS mimi.execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES mimi.projects(id) ON DELETE CASCADE,
    task_id UUID REFERENCES mimi.tasks(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES mimi.agents(id) ON DELETE SET NULL,
    log_type VARCHAR(50) NOT NULL,
    message TEXT,
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_projects_name ON mimi.projects(name);
CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON mimi.tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON mimi.tasks(status);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_task_id ON mimi.task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_depends_on_task_id ON mimi.task_dependencies(depends_on_task_id);
CREATE INDEX IF NOT EXISTS idx_agents_name ON mimi.agents(name);
CREATE INDEX IF NOT EXISTS idx_artifacts_project_id ON mimi.artifacts(project_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_task_id ON mimi.artifacts(task_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_project_id ON mimi.execution_logs(project_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_task_id ON mimi.execution_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_timestamp ON mimi.execution_logs(timestamp);

-- Add updated_at trigger function
CREATE OR REPLACE FUNCTION mimi.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON mimi.projects FOR EACH ROW EXECUTE FUNCTION mimi.update_updated_at_column();
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON mimi.tasks FOR EACH ROW EXECUTE FUNCTION mimi.update_updated_at_column();
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON mimi.agents FOR EACH ROW EXECUTE FUNCTION mimi.update_updated_at_column();
CREATE TRIGGER update_artifacts_updated_at BEFORE UPDATE ON mimi.artifacts FOR EACH ROW EXECUTE FUNCTION mimi.update_updated_at_column(); 