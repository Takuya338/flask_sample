# Flask + MySQL Docker Development Environment

This is a multi-container Flask application with MySQL database and Selenium UI testing. The architecture uses Docker Compose for orchestration with development-optimized configurations.

## Architecture & Data Flow

**Core Services:**
- `app`: Flask web server (Python 3.11.4) with live reload via volume mounting
- `db`: MySQL 8.0 with native password authentication and initialization scripts
- `selenium` + `ui-tests`: Selenium Grid for automated UI testing (test profile only)

**Key Integration Points:**
- Flask connects to MySQL using PyMySQL with environment-based configuration
- Database initialization happens automatically via `/docker-entrypoint-initdb.d` mounting
- UI tests use remote WebDriver against headless Chrome in separate container

## Development Workflow

**Start Development Environment:**
```bash
docker compose up --build  # Rebuilds app container, starts app + db
```

**Database Operations:**
```bash
# Connect to MySQL from host
mysql -h 127.0.0.1 -P 3306 -u mysql -p

# Connect from container
docker compose exec db mysql -u mysql -pmysql mysql

# Reset database (destroys data)
docker compose down -v && docker compose up --build
```

**UI Testing Workflow:**
```bash
# 1. Start core services
docker compose up -d app db

# 2. Start Selenium (test profile)
docker compose --profile test up -d selenium  

# 3. Run UI tests
docker compose --profile test run --rm ui-tests

# 4. Cleanup test services
docker compose --profile test stop selenium
```

## Project-Specific Patterns

**Environment Configuration:**
- All services use consistent `MYSQL_*` environment variables in `compose.yaml`
- Flask app supports `.env` files via `python-dotenv` for local overrides
- Database credentials: `mysql/mysql/mysql` (user/password/database)

**Volume Mounting Strategy:**
- `./app:/app` - Live reload for Flask development
- `./db:/docker-entrypoint-initdb.d` - Automatic SQL script execution
- `mysql_data` - Persistent database storage

**Testing Architecture:**
- UI tests in `tests/ui/` use pytest + Selenium WebDriver
- Tests include retry logic and service availability checks (`_wait_for_http`)
- Selenium runs headless Chrome with 2GB shared memory allocation

**Database Schema:**
- Default table: `products` (id, name, price, description, created_at)
- Schema defined in `db/init.sql`, executed on first container startup

## Common Operations

**Add Dependencies:**
1. Update `requirements.txt`
2. Run `docker compose up --build` to rebuild app container

**Debug Flask Application:**
- Logs: `docker compose logs app -f`
- Flask routes: `docker compose exec app flask routes`
- Interactive shell: `docker compose exec app python`

**Database Schema Changes:**
1. Modify `db/init.sql`
2. Reset database: `docker compose down -v && docker compose up --build`

**Port Mappings:**
- Flask: `localhost:5000`  
- MySQL: `localhost:3306`
- Selenium Hub: `localhost:4444` (test profile only)

## Development Guidelines

**Implementation Requirements:**
- All implementation must be done within Docker containers

**Testing Requirements:**
- Always create test code after implementation
- Implement the following test types:
  - Unit tests for individual methods
  - Functional tests for feature-level functionality
  - UI tests for user interface validation
  - E2E (End-to-End) tests for complete workflows
  - Scenario tests for business logic validation

**Code Quality Standards:**
- Follow PEP8 coding conventions for all Python code
- Write reviews and comments in Japanese

**Requirements Implementation:**
- Implement necessary features to satisfy the requirements specified in 要求内容.md