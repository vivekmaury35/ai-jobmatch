import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.skill import Skill

def get_skills_data():
    return [
        {"canonical": "python", "display": "Python", "category": "language", "aliases": ["python3", "python 3", "py"]},
        {"canonical": "javascript", "display": "JavaScript", "category": "language", "aliases": ["js", "es6", "vanilla js"]},
        {"canonical": "typescript", "display": "TypeScript", "category": "language", "aliases": ["ts", "typescript 4"]},
        {"canonical": "java", "display": "Java", "category": "language", "aliases": ["java 8", "java 11", "java 17", "j2ee"]},
        {"canonical": "postgresql", "display": "PostgreSQL", "category": "database", "aliases": ["postgres", "pgsql", "postgre sql"]},
        {"canonical": "mysql", "display": "MySQL", "category": "database", "aliases": ["my sql"]},
        {"canonical": "mongodb", "display": "MongoDB", "category": "database", "aliases": ["mongo", "mongo db"]},
        {"canonical": "react", "display": "React", "category": "frontend", "aliases": ["reactjs", "react.js", "react js"]},
        {"canonical": "nextjs", "display": "Next.js", "category": "frontend", "aliases": ["next.js", "nextjs", "next app router"]},
        {"canonical": "fastapi", "display": "FastAPI", "category": "backend", "aliases": ["fast api"]},
        {"canonical": "django", "display": "Django", "category": "backend", "aliases": ["django framework"]},
        {"canonical": "flask", "display": "Flask", "category": "backend", "aliases": ["flask framework"]},
        {"canonical": "expressjs", "display": "Express.js", "category": "backend", "aliases": ["express", "express.js", "expressjs"]},
        {"canonical": "nodejs", "display": "Node.js", "category": "backend", "aliases": ["node", "node.js", "nodejs"]},
        {"canonical": "docker", "display": "Docker", "category": "infrastructure", "aliases": ["docker compose", "docker container"]},
        {"canonical": "kubernetes", "display": "Kubernetes", "category": "infrastructure", "aliases": ["k8s", "kube"]},
        {"canonical": "aws", "display": "AWS", "category": "cloud", "aliases": ["amazon web services", "aws cloud"]},
        {"canonical": "azure", "display": "Azure", "category": "cloud", "aliases": ["microsoft azure"]},
        {"canonical": "gcp", "display": "GCP", "category": "cloud", "aliases": ["google cloud platform", "google cloud"]},
        {"canonical": "git", "display": "Git", "category": "tooling", "aliases": ["github", "gitlab", "bitbucket"]},
        {"canonical": "html", "display": "HTML", "category": "frontend", "aliases": ["html5", "html 5"]},
        {"canonical": "css", "display": "CSS", "category": "frontend", "aliases": ["css3", "css 3"]},
        {"canonical": "tailwindcss", "display": "Tailwind CSS", "category": "frontend", "aliases": ["tailwind", "tailwind.css"]},
        {"canonical": "linux", "display": "Linux", "category": "system", "aliases": ["ubuntu", "debian", "centos"]},
        {"canonical": "sql", "display": "SQL", "category": "language", "aliases": ["structured query language"]},
        {"canonical": "graphql", "display": "GraphQL", "category": "api", "aliases": ["graph ql"]},
        {"canonical": "restapi", "display": "REST API", "category": "api", "aliases": ["rest", "restful", "restful api"]},
        {"canonical": "redis", "display": "Redis", "category": "database", "aliases": ["redis cache"]},
        {"canonical": "csharp", "display": "C#", "category": "language", "aliases": ["c sharp", "c#.net"]},
        {"canonical": "dotnet", "display": ".NET", "category": "framework", "aliases": ["dotnet core", ".net core", "asp.net"]},
        # Add ~70 more to cross the 100 mark
        {"canonical": "cpp", "display": "C++", "category": "language", "aliases": ["c plus plus", "c/c++"]},
        {"canonical": "c", "display": "C", "category": "language", "aliases": []},
        {"canonical": "php", "display": "PHP", "category": "language", "aliases": ["php 7", "php 8"]},
        {"canonical": "ruby", "display": "Ruby", "category": "language", "aliases": ["ruby 3"]},
        {"canonical": "rubyonrails", "display": "Ruby on Rails", "category": "backend", "aliases": ["rails", "ror"]},
        {"canonical": "go", "display": "Go", "category": "language", "aliases": ["golang"]},
        {"canonical": "rust", "display": "Rust", "category": "language", "aliases": ["rustlang"]},
        {"canonical": "kotlin", "display": "Kotlin", "category": "language", "aliases": []},
        {"canonical": "swift", "display": "Swift", "category": "language", "aliases": ["swiftui"]},
        {"canonical": "dart", "display": "Dart", "category": "language", "aliases": []},
        {"canonical": "flutter", "display": "Flutter", "category": "mobile", "aliases": []},
        {"canonical": "reactnative", "display": "React Native", "category": "mobile", "aliases": ["react-native", "rn"]},
        {"canonical": "vuejs", "display": "Vue.js", "category": "frontend", "aliases": ["vue", "vue3", "vue 3"]},
        {"canonical": "angular", "display": "Angular", "category": "frontend", "aliases": ["angularjs", "angular 2+"]},
        {"canonical": "svelte", "display": "Svelte", "category": "frontend", "aliases": ["sveltekit"]},
        {"canonical": "jquery", "display": "jQuery", "category": "frontend", "aliases": ["j query"]},
        {"canonical": "bootstrap", "display": "Bootstrap", "category": "frontend", "aliases": ["twitter bootstrap"]},
        {"canonical": "sass", "display": "Sass", "category": "frontend", "aliases": ["scss"]},
        {"canonical": "materialui", "display": "Material-UI", "category": "frontend", "aliases": ["mui", "material ui"]},
        {"canonical": "spring", "display": "Spring", "category": "backend", "aliases": ["spring boot", "springboot"]},
        {"canonical": "hibernate", "display": "Hibernate", "category": "backend", "aliases": ["jpa", "hibernate orm"]},
        {"canonical": "laravel", "display": "Laravel", "category": "backend", "aliases": []},
        {"canonical": "elasticsearch", "display": "Elasticsearch", "category": "database", "aliases": ["elastic search", "elk"]},
        {"canonical": "cassandra", "display": "Cassandra", "category": "database", "aliases": ["apache cassandra"]},
        {"canonical": "dynamodb", "display": "DynamoDB", "category": "database", "aliases": ["aws dynamodb", "amazon dynamodb"]},
        {"canonical": "sqlite", "display": "SQLite", "category": "database", "aliases": ["sqlite3"]},
        {"canonical": "mariadb", "display": "MariaDB", "category": "database", "aliases": ["maria db"]},
        {"canonical": "oracle", "display": "Oracle", "category": "database", "aliases": ["oracle db", "oracledb"]},
        {"canonical": "kafka", "display": "Kafka", "category": "infrastructure", "aliases": ["apache kafka"]},
        {"canonical": "rabbitmq", "display": "RabbitMQ", "category": "infrastructure", "aliases": ["rabbit mq"]},
        {"canonical": "nginx", "display": "NGINX", "category": "infrastructure", "aliases": []},
        {"canonical": "apache", "display": "Apache", "category": "infrastructure", "aliases": ["httpd", "apache http server"]},
        {"canonical": "terraform", "display": "Terraform", "category": "infrastructure", "aliases": ["hashicorp terraform"]},
        {"canonical": "ansible", "display": "Ansible", "category": "infrastructure", "aliases": []},
        {"canonical": "dockercompose", "display": "Docker Compose", "category": "infrastructure", "aliases": ["docker-compose"]},
        {"canonical": "jenkins", "display": "Jenkins", "category": "tooling", "aliases": ["jenkins ci"]},
        {"canonical": "gitlabci", "display": "GitLab CI", "category": "tooling", "aliases": ["gitlab ci/cd"]},
        {"canonical": "githubactions", "display": "GitHub Actions", "category": "tooling", "aliases": ["gh actions"]},
        {"canonical": "jira", "display": "Jira", "category": "tooling", "aliases": ["atlassian jira"]},
        {"canonical": "webpack", "display": "Webpack", "category": "tooling", "aliases": []},
        {"canonical": "vite", "display": "Vite", "category": "tooling", "aliases": ["vitejs", "vite.js"]},
        {"canonical": "babel", "display": "Babel", "category": "tooling", "aliases": ["babeljs"]},
        {"canonical": "jest", "display": "Jest", "category": "testing", "aliases": ["jest core"]},
        {"canonical": "cypress", "display": "Cypress", "category": "testing", "aliases": ["cypress.io"]},
        {"canonical": "playwright", "display": "Playwright", "category": "testing", "aliases": []},
        {"canonical": "selenium", "display": "Selenium", "category": "testing", "aliases": ["selenium webdriver"]},
        {"canonical": "mocha", "display": "Mocha", "category": "testing", "aliases": ["mochajs"]},
        {"canonical": "pytest", "display": "Pytest", "category": "testing", "aliases": ["py.test"]},
        {"canonical": "junit", "display": "JUnit", "category": "testing", "aliases": ["junit4", "junit5"]},
        {"canonical": "machinelearning", "display": "Machine Learning", "category": "data", "aliases": ["ml"]},
        {"canonical": "artificialintelligence", "display": "Artificial Intelligence", "category": "data", "aliases": ["ai"]},
        {"canonical": "deeplearning", "display": "Deep Learning", "category": "data", "aliases": ["dl"]},
        {"canonical": "datamining", "display": "Data Mining", "category": "data", "aliases": []},
        {"canonical": "dataanalysis", "display": "Data Analysis", "category": "data", "aliases": ["data analytics"]},
        {"canonical": "pandas", "display": "Pandas", "category": "data", "aliases": []},
        {"canonical": "numpy", "display": "NumPy", "category": "data", "aliases": []},
        {"canonical": "scikitlearn", "display": "Scikit-Learn", "category": "data", "aliases": ["sklearn", "scikit learn"]},
        {"canonical": "tensorflow", "display": "TensorFlow", "category": "data", "aliases": ["tf", "tensor flow"]},
        {"canonical": "pytorch", "display": "PyTorch", "category": "data", "aliases": ["torch"]},
        {"canonical": "keras", "display": "Keras", "category": "data", "aliases": []},
        {"canonical": "opencv", "display": "OpenCV", "category": "data", "aliases": ["open cv"]},
        {"canonical": "apachespark", "display": "Apache Spark", "category": "data", "aliases": ["spark", "pyspark"]},
        {"canonical": "hadoop", "display": "Hadoop", "category": "data", "aliases": ["apache hadoop"]},
        {"canonical": "airflow", "display": "Airflow", "category": "data", "aliases": ["apache airflow"]},
        {"canonical": "tableau", "display": "Tableau", "category": "data", "aliases": []},
        {"canonical": "powerbi", "display": "Power BI", "category": "data", "aliases": ["powerbi", "ms power bi"]},
        {"canonical": "devops", "display": "DevOps", "category": "methodology", "aliases": ["development operations"]},
        {"canonical": "agile", "display": "Agile", "category": "methodology", "aliases": ["agile methodology"]},
        {"canonical": "scrum", "display": "Scrum", "category": "methodology", "aliases": ["scrum framework"]},
        {"canonical": "kanban", "display": "Kanban", "category": "methodology", "aliases": []},
        {"canonical": "tdd", "display": "TDD", "category": "methodology", "aliases": ["test driven development", "test-driven development"]},
        {"canonical": "ci_cd", "display": "CI/CD", "category": "methodology", "aliases": ["continuous integration", "continuous deployment"]},
        {"canonical": "microservices", "display": "Microservices", "category": "architecture", "aliases": ["microservices architecture"]},
        {"canonical": "serverless", "display": "Serverless", "category": "architecture", "aliases": ["serverless computing"]},
        {"canonical": "bash", "display": "Bash", "category": "system", "aliases": ["shell script", "bash scripting"]},
        {"canonical": "powershell", "display": "PowerShell", "category": "system", "aliases": ["windows powershell"]},
        {"canonical": "firebase", "display": "Firebase", "category": "cloud", "aliases": []},
        {"canonical": "supabase", "display": "Supabase", "category": "cloud", "aliases": []},
        {"canonical": "heroku", "display": "Heroku", "category": "cloud", "aliases": []},
        {"canonical": "vercel", "display": "Vercel", "category": "cloud", "aliases": []},
        {"canonical": "netlify", "display": "Netlify", "category": "cloud", "aliases": []},
    ]

def seed():
    print("Seeding skills taxonomy...")
    db: Session = SessionLocal()

    try:
        skills_data = get_skills_data()

        # Keep track of counts
        added = 0
        skipped = 0

        for item in skills_data:
            # Check if skill already exists
            existing = db.query(Skill).filter(Skill.canonical_name == item["canonical"]).first()
            if existing:
                skipped += 1
                continue

            skill = Skill(
                canonical_name=item["canonical"],
                display_name=item["display"],
                category=item["category"],
                aliases=item["aliases"]
            )
            db.add(skill)
            added += 1

        db.commit()
        print(f"Seed complete. Added {added} skills. Skipped {skipped} existing.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding skills: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
