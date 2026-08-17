CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS sessions (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS skills (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    canonical_name VARCHAR NOT NULL,
    display_name VARCHAR NOT NULL,
    aliases VARCHAR[],
    category VARCHAR,
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_skills_canonical_name ON skills (canonical_name);

CREATE TABLE IF NOT EXISTS jobs (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,
    title VARCHAR,
    raw_text VARCHAR NOT NULL,
    parsed_data JSONB,
    content_hash VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id),
    CONSTRAINT fk_jobs_session_id FOREIGN KEY(session_id) REFERENCES sessions (id)
);
CREATE INDEX IF NOT EXISTS ix_jobs_content_hash ON jobs (content_hash);
CREATE INDEX IF NOT EXISTS ix_jobs_session_id ON jobs (session_id);

CREATE TABLE IF NOT EXISTS resumes (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,
    filename VARCHAR NOT NULL,
    raw_text VARCHAR NOT NULL,
    parsed_data JSONB,
    content_hash VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id),
    CONSTRAINT fk_resumes_session_id FOREIGN KEY(session_id) REFERENCES sessions (id)
);
CREATE INDEX IF NOT EXISTS ix_resumes_content_hash ON resumes (content_hash);
CREATE INDEX IF NOT EXISTS ix_resumes_session_id ON resumes (session_id);

CREATE TABLE IF NOT EXISTS analyses (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,
    resume_id UUID NOT NULL,
    job_id UUID NOT NULL,
    overall_score FLOAT,
    skill_score FLOAT,
    semantic_score FLOAT,
    experience_score FLOAT,
    education_score FLOAT,
    project_evidence_score FLOAT,
    matched_skills JSONB,
    missing_skills JSONB,
    explanation VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id),
    CONSTRAINT fk_analyses_job_id FOREIGN KEY(job_id) REFERENCES jobs (id),
    CONSTRAINT fk_analyses_resume_id FOREIGN KEY(resume_id) REFERENCES resumes (id),
    CONSTRAINT fk_analyses_session_id FOREIGN KEY(session_id) REFERENCES sessions (id)
);
CREATE INDEX IF NOT EXISTS ix_analyses_session_id ON analyses (session_id);

CREATE TABLE IF NOT EXISTS job_skills (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL,
    skill_id UUID,
    raw_text VARCHAR NOT NULL,
    required BOOLEAN,
    importance FLOAT,
    PRIMARY KEY (id),
    CONSTRAINT fk_job_skills_job_id FOREIGN KEY(job_id) REFERENCES jobs (id),
    CONSTRAINT fk_job_skills_skill_id FOREIGN KEY(skill_id) REFERENCES skills (id)
);

CREATE TABLE IF NOT EXISTS resume_skills (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    resume_id UUID NOT NULL,
    skill_id UUID,
    raw_text VARCHAR NOT NULL,
    evidence_source VARCHAR NOT NULL,
    confidence FLOAT NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_resume_skills_resume_id FOREIGN KEY(resume_id) REFERENCES resumes (id),
    CONSTRAINT fk_resume_skills_skill_id FOREIGN KEY(skill_id) REFERENCES skills (id)
);

CREATE TABLE IF NOT EXISTS recommendations (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL,
    type VARCHAR NOT NULL,
    content VARCHAR NOT NULL,
    priority INTEGER,
    PRIMARY KEY (id),
    CONSTRAINT fk_recommendations_analysis_id FOREIGN KEY(analysis_id) REFERENCES analyses (id)
);

INSERT INTO skills (canonical_name, display_name, category) VALUES ('python', 'Python', 'language') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('javascript', 'JavaScript', 'language') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('typescript', 'TypeScript', 'language') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('java', 'Java', 'language') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('postgresql', 'PostgreSQL', 'database') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('mysql', 'MySQL', 'database') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('mongodb', 'MongoDB', 'database') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('react', 'React', 'frontend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('nextjs', 'Next.js', 'frontend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('fastapi', 'FastAPI', 'backend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('django', 'Django', 'backend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('flask', 'Flask', 'backend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('expressjs', 'Express.js', 'backend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('nodejs', 'Node.js', 'backend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('docker', 'Docker', 'infrastructure') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('kubernetes', 'Kubernetes', 'infrastructure') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('aws', 'AWS', 'cloud') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('azure', 'Azure', 'cloud') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('gcp', 'GCP', 'cloud') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('git', 'Git', 'tooling') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('html', 'HTML', 'frontend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('css', 'CSS', 'frontend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('tailwindcss', 'Tailwind CSS', 'frontend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('linux', 'Linux', 'system') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('sql', 'SQL', 'language') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('graphql', 'GraphQL', 'api') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('restapi', 'REST API', 'api') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('redis', 'Redis', 'database') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('csharp', 'C#', 'language') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('dotnet', '.NET', 'framework') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('cpp', 'C++', 'language') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('c', 'C', 'language') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('php', 'PHP', 'language') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('ruby', 'Ruby', 'language') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('rubyonrails', 'Ruby on Rails', 'backend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('go', 'Go', 'language') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('rust', 'Rust', 'language') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('kotlin', 'Kotlin', 'language') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('swift', 'Swift', 'language') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('dart', 'Dart', 'language') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('flutter', 'Flutter', 'mobile') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('reactnative', 'React Native', 'mobile') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('vuejs', 'Vue.js', 'frontend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('angular', 'Angular', 'frontend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('svelte', 'Svelte', 'frontend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('jquery', 'jQuery', 'frontend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('bootstrap', 'Bootstrap', 'frontend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('sass', 'Sass', 'frontend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('materialui', 'Material-UI', 'frontend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('spring', 'Spring', 'backend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('hibernate', 'Hibernate', 'backend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('laravel', 'Laravel', 'backend') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('elasticsearch', 'Elasticsearch', 'database') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('cassandra', 'Cassandra', 'database') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('dynamodb', 'DynamoDB', 'database') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('sqlite', 'SQLite', 'database') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('mariadb', 'MariaDB', 'database') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('oracle', 'Oracle', 'database') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('kafka', 'Kafka', 'infrastructure') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('rabbitmq', 'RabbitMQ', 'infrastructure') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('nginx', 'NGINX', 'infrastructure') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('apache', 'Apache', 'infrastructure') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('terraform', 'Terraform', 'infrastructure') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('ansible', 'Ansible', 'infrastructure') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('dockercompose', 'Docker Compose', 'infrastructure') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('jenkins', 'Jenkins', 'tooling') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('gitlabci', 'GitLab CI', 'tooling') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('githubactions', 'GitHub Actions', 'tooling') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('jira', 'Jira', 'tooling') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('webpack', 'Webpack', 'tooling') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('vite', 'Vite', 'tooling') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('babel', 'Babel', 'tooling') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('jest', 'Jest', 'testing') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('cypress', 'Cypress', 'testing') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('playwright', 'Playwright', 'testing') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('selenium', 'Selenium', 'testing') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('mocha', 'Mocha', 'testing') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('pytest', 'Pytest', 'testing') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('junit', 'JUnit', 'testing') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('machinelearning', 'Machine Learning', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('artificialintelligence', 'Artificial Intelligence', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('deeplearning', 'Deep Learning', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('datamining', 'Data Mining', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('dataanalysis', 'Data Analysis', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('pandas', 'Pandas', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('numpy', 'NumPy', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('scikitlearn', 'Scikit-Learn', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('tensorflow', 'TensorFlow', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('pytorch', 'PyTorch', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('keras', 'Keras', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('opencv', 'OpenCV', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('apachespark', 'Apache Spark', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('hadoop', 'Hadoop', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('airflow', 'Airflow', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('tableau', 'Tableau', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('powerbi', 'Power BI', 'data') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('devops', 'DevOps', 'methodology') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('agile', 'Agile', 'methodology') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('scrum', 'Scrum', 'methodology') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('kanban', 'Kanban', 'methodology') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('tdd', 'TDD', 'methodology') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('ci_cd', 'CI/CD', 'methodology') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('microservices', 'Microservices', 'architecture') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('serverless', 'Serverless', 'architecture') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('bash', 'Bash', 'system') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('powershell', 'PowerShell', 'system') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('firebase', 'Firebase', 'cloud') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('supabase', 'Supabase', 'cloud') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('heroku', 'Heroku', 'cloud') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('vercel', 'Vercel', 'cloud') ON CONFLICT DO NOTHING;
INSERT INTO skills (canonical_name, display_name, category) VALUES ('netlify', 'Netlify', 'cloud') ON CONFLICT DO NOTHING;
