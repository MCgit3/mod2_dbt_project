# mod2_dbt_project - Design Document

## Table of Contents
1. [Project Overview](#project-overview)
2. [Setup & Installation](#setup--installation)
3. [File Documentation](#file-documentation)
4. [Project Structure](#project-structure)
5. [Common Commands](#common-commands)
6. [Key Features](#key-features)
7. [Architecture](#architecture)
8. [Deployment Pipeline](#deployment-pipeline)
9. [Next Steps](#next-steps)
10. [Troubleshooting](#troubleshooting)

---

## Project Overview

This is a **dbt (data build tool) project** designed to work with **Google BigQuery** for data transformation and modeling. The project is containerized using Docker and configured for automated deployment via Google Cloud Build to Cloud Run.

### Key Technologies
- **dbt-bigquery 1.11.1** — Data transformation framework
- **Google BigQuery** — Data warehouse and query engine
- **Docker** — Container orchestration
- **Google Cloud Build** — CI/CD pipeline
- **Google Cloud Run** — Serverless job execution
- **Python 3.11** — Runtime environment

### Target Use Case
ETL/ELT pipelines transforming raw data in BigQuery into clean, modeled tables for analytics and reporting.

---

## Setup & Installation

### Prerequisites
- Docker installed locally (for containerized development)
- Google Cloud account with BigQuery enabled
- Service account JSON credentials with BigQuery permissions
- Python 3.11+ (for local development without Docker)
- Git for version control

### Local Setup (Without Docker)

#### Step 1: Clone the Repository
```bash
git clone https://github.com/MCgit3/mod2_dbt_project.git
cd mod2_dbt_project
```

#### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

This installs `dbt-bigquery==1.11.1`, which allows dbt to communicate with Google BigQuery.

#### Step 3: Prepare Google Cloud Credentials
1. Create or download a service account JSON from Google Cloud Console
2. Place the JSON file in a secure location (e.g., `/path/to/service-account.json`)
3. Set the environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   ```

#### Step 4: Configure dbt Profile
Edit `profiles.yml` with your GCP project details:
```yaml
my_project:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: your-gcp-project-id       # Update this
      dataset: your_dataset_name         # Update this
      keyfile: /path/to/service-account.json  # Update this
      threads: 4
      timeout_seconds: 300
```

#### Step 5: Verify Connection
```bash
dbt debug
```

This command verifies your BigQuery connection is working correctly.

#### Step 6: Run Initial Commands
```bash
dbt run      # Execute dbt models
dbt test     # Run data quality tests
```

---

### Docker Setup (Recommended for Production)

#### Step 1: Build the Docker Image
```bash
docker build -t dbt-runner .
```

#### Step 2: Prepare Service Account
Copy your service account JSON into the project root:
```bash
cp /path/to/service-account.json ./service-account.json
```

#### Step 3: Run the Container
```bash
docker run \
  -v $(pwd)/service-account.json:/app/service-account.json \
  dbt-runner dbt run
```

#### Step 4: Override Default Command
The default command is `dbt run`, but you can override it:
```bash
# Run tests instead
docker run \
  -v $(pwd)/service-account.json:/app/service-account.json \
  dbt-runner dbt test

# Run specific model
docker run \
  -v $(pwd)/service-account.json:/app/service-account.json \
  dbt-runner dbt run --select model_name
```

---

### Google Cloud Deployment

#### Prerequisites
- Google Cloud project with owner or editor permissions
- Cloud Build API enabled
- Cloud Run API enabled
- Artifact Registry API enabled

#### Step 1: Create Service Account for dbt
```bash
gcloud iam service-accounts create dbt-runner \
  --display-name="dbt Runner Service Account"

# Grant BigQuery permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:dbt-runner@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"
```

#### Step 2: Configure Cloud Build
Update `cloudbuild.yaml` with your project details:
```yaml
- '--image=gcr.io/YOUR_PROJECT_ID/dbt-runner'
- '--service-account=dbt-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com'
```

#### Step 3: Connect GitHub Repository
1. Navigate to Cloud Build in Google Cloud Console
2. Connect your GitHub repository
3. Create a build trigger for the main branch

#### Step 4: Deploy
Push changes to GitHub:
```bash
git push origin main
```

Cloud Build automatically triggers, builds the image, and deploys to Cloud Run.

#### Step 5: Monitor Deployment
```bash
# View Cloud Run Jobs
gcloud run jobs list

# View job execution logs
gcloud run jobs log dbt-job --region=us-central1
```

---

## File Documentation

### Configuration Files

#### `dbt_project.yml`
**Location:** Repository root  
**Type:** YAML configuration  
**Purpose:** Central configuration for the entire dbt project

**Key Sections:**
```yaml
name: 'my_project'              # Project identifier (lowercase, underscores only)
version: '1.0.0'                # Semantic versioning
profile: 'my_project'           # References profile in profiles.yml

model-paths: ["models"]         # Where dbt finds SQL models
analysis-paths: ["analyses"]    # Where ad-hoc queries go
test-paths: ["tests"]           # Where tests are defined
seed-paths: ["seeds"]           # Where CSV seed data lives
macro-paths: ["macros"]         # Where Jinja2 macros are defined
snapshot-paths: ["snapshots"]   # Where snapshots are defined

clean-targets:                  # Directories removed by dbt clean
  - "target"                    # Compiled SQL and artifacts
  - "dbt_packages"              # Downloaded dependencies

models:
  my_project:
    example:
      +materialized: view       # Default materialization for example folder
```

**What to Update:**
- Change `name` to match your project name
- Adjust path configurations if using different directory structures
- Modify model materialization (view/table/incremental) as needed

---

#### `profiles.yml`
**Location:** Repository root  
**Type:** YAML configuration  
**Purpose:** Database connection configuration for dbt

**Current Configuration:**
```yaml
my_project:
  target: dev                   # Active target/environment
  outputs:
    dev:
      type: bigquery            # Database type
      method: service-account   # Authentication method
      project: hale-badge-505304-j8           # GCP Project ID
      dataset: olist_dataset_mod2             # BigQuery dataset
      keyfile: /mnt/c/Mythili/NTU/Module_2/hale-badge-505304-j8-6583941cdaca.json
      threads: 4                # Parallel execution threads
      timeout_seconds: 300      # Query timeout
```

**Fields Explained:**
- **type:** Database adapter (bigquery for this project)
- **method:** How to authenticate (service-account uses JSON key)
- **project:** Your GCP project ID
- **dataset:** Target BigQuery dataset where models will be created
- **keyfile:** Path to service account JSON credentials
- **threads:** Number of simultaneous model executions (higher = faster, use 4-8)
- **timeout_seconds:** Maximum time for a single query before timing out

⚠️ **Security Warning:** Never commit credentials to version control. Use environment variables or secrets management instead:
```yaml
my_project:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: "{{ env_var('GCP_PROJECT_ID') }}"
      dataset: "{{ env_var('GCP_DATASET') }}"
      keyfile: "{{ env_var('GOOGLE_APPLICATION_CREDENTIALS') }}"
      threads: 4
      timeout_seconds: 300
```

---

#### `requirements.txt`
**Location:** Repository root  
**Type:** Python pip requirements  
**Purpose:** Declares Python package dependencies

**Current Content:**
```
dbt-bigquery==1.11.1
```

**What This Does:**
- Specifies exact version of dbt-bigquery to install
- Ensures consistency across development and production environments
- Installing this package automatically includes dbt-core as a dependency

**To Add Dependencies:**
```
dbt-bigquery==1.11.1
dbt-utils==1.1.1          # Common macros and tests
dbt-artifacts==0.8.0      # Artifact management
dbt-power-user==0.5.1     # Enhanced functionality
```

---

### Docker & Deployment Files

#### `Dockerfile`
**Location:** Repository root  
**Type:** Docker container configuration  
**Purpose:** Defines the container image for running dbt in production

**File Breakdown:**
```dockerfile
FROM python:3.11-slim
# - Start with lightweight Python 3.11 image
# - 'slim' variant reduces image size (~300MB vs 900MB)

RUN pip install --no-cache-dir dbt-bigquery==1.11.1
# - Install dbt-bigquery package
# - --no-cache-dir reduces layer size

WORKDIR /app
# - Set working directory inside container
# - All subsequent commands run from this directory

COPY . /app
# - Copy entire project into container at /app
# - Includes all dbt models, macros, configurations, etc.

ENV GOOGLE_APPLICATION_CREDENTIALS=/app/service-account.json
# - Tell Google libraries where to find credentials
# - Path must match where credentials are mounted

CMD ["dbt", "run"]
# - Default command when container starts
# - Can be overridden: docker run ... dbt test
```

**Common Usage:**
```bash
# Build image
docker build -t dbt-runner .

# Run dbt run (default)
docker run dbt-runner

# Run dbt test
docker run dbt-runner dbt test

# Run dbt debug
docker run dbt-runner dbt debug

# With volume mount for logs
docker run -v $(pwd)/logs:/app/logs dbt-runner dbt run
```

**Production Considerations:**
- Image size: ~400MB (Python 3.11 slim + dbt-bigquery)
- Build time: ~2-3 minutes
- Runtime: Depends on number and complexity of models
- Resource limits: Recommend 2+ GB memory, 2+ CPU cores

---

#### `cloudbuild.yaml`
**Location:** Repository root  
**Type:** Google Cloud Build configuration  
**Purpose:** Defines CI/CD pipeline for automated deployment

**Pipeline Steps Explained:**

**Step 1: Build Docker Image**
```yaml
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/dbt-runner', '.']
```
- Uses Google Cloud Builder's Docker image
- Builds Dockerfile in current directory
- Tags image with project ID and repository name
- `$PROJECT_ID` is automatically substituted by Cloud Build

**Step 2: Push Image to Registry**
```yaml
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/$PROJECT_ID/dbt-runner']
```
- Pushes built image to Google Artifact Registry (Container Registry)
- Makes image available for Cloud Run to deploy

**Step 3: Deploy to Cloud Run Job**
```yaml
- name: 'gcr.io/cloud-builders/gcloud'
  args:
    - 'run'
    - 'jobs'
    - 'update'
    - 'dbt-job'                              # Job name
    - '--image=gcr.io/$PROJECT_ID/dbt-runner'  # Image to deploy
    - '--region=us-central1'                 # GCP region
    - '--service-account=dbt-runner@${PROJECT_ID}.iam.gserviceaccount.com'  # Auth
```
- Updates Cloud Run Job with new image
- Cloud Run Jobs are suitable for batch/scheduled workloads
- Service account handles GCP authentication

**Logging Configuration:**
```yaml
options:
  logging: CLOUD_LOGGING_ONLY
```
- Sends all logs to Google Cloud Logging (Stackdriver)
- Accessible via Cloud Console

**Complete Workflow:**
```
git push → Cloud Build triggered → Docker image built → 
Image pushed to Artifact Registry → Cloud Run Job updated → 
Job runs dbt commands → Results logged
```

**Customization:**
```yaml
# Change target region
- '--region=us-west1'

# Add memory/CPU limits
- '--memory=4Gi'
- '--cpu=2'

# Set environment variables
- '--set-env-vars=DBT_THREADS=8'
```

---

### Git Configuration Files

#### `.gitignore`
**Location:** Repository root  
**Type:** Git configuration  
**Purpose:** Prevents committing unnecessary/sensitive files

**Contents:**
```
target/           # dbt build artifacts (compiled SQL)
dbt_packages/     # Downloaded package dependencies
logs/             # Execution logs
```

**Why These Are Ignored:**
- **target/:** Contains compiled SQL files generated during `dbt run` — not needed in version control
- **dbt_packages/:** External dependencies installed by `dbt deps` — can be reinstalled anytime
- **logs/:** Execution logs specific to each run — clutters repository history

**Additional Recommendations:**
```
.env              # Local environment variables (NEVER commit!)
profiles.yml      # If using actual credentials (use env vars instead)
*.json            # Service account credentials
.DS_Store         # macOS metadata
*.log             # Log files
```

---

#### `.user.yml`
**Location:** Repository root  
**Type:** dbt metadata  
**Purpose:** Stores unique project identifier

**Content:**
```yaml
id: f938bde4-bb34-4edc-9f5d-b74a02742761
```

**What It Does:**
- Auto-generated by dbt during project initialization
- Used internally by dbt Cloud for project tracking
- Enables dbt to identify this project uniquely
- Safe to commit to version control

---

#### `README.md`
**Location:** Repository root  
**Type:** Markdown documentation  
**Purpose:** Quick start guide and project introduction

**Current Content:**
- Welcome message
- Basic commands (`dbt run`, `dbt test`)
- Links to dbt documentation and community

**Recommended Enhancements:**
- Add project description
- Include architecture diagram
- Document data sources and transformations
- Provide troubleshooting guide

---

## Project Structure

### Directory Layout
```
mod2_dbt_project/
├── models/               # SQL transformation models (currently empty)
├── tests/                # Data quality tests (currently empty)
├── seeds/                # CSV seed data (currently empty)
├── macros/               # Reusable Jinja2 functions (currently empty)
├── analyses/             # Ad-hoc analysis queries (currently empty)
├── snapshots/            # Slowly changing dimension configs (currently empty)
├── target/               # Build artifacts (generated, git-ignored)
├── dbt_packages/         # Downloaded packages (generated, git-ignored)
├── logs/                 # Execution logs (generated, git-ignored)
│
├── dbt_project.yml       # Project configuration
├── profiles.yml          # Database connection config
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container specification
├── cloudbuild.yaml       # CI/CD pipeline
│
├── .gitignore            # Git ignore rules
├── .user.yml             # dbt project ID
└── README.md             # Project overview
```

### Directory Purposes

#### `models/`
Where you define dbt models (SQL transformations).

**Example Structure:**
```
models/
├── staging/
│   ├── stg_customers.sql
│   └── stg_orders.sql
├── marts/
│   ├── fact_orders.sql
│   └── dim_customers.sql
└── schema.yml          # Model documentation and tests
```

#### `tests/`
Data quality tests to ensure models are correct.

**Example:**
```
tests/
├── assert_positive_revenue.sql
└── assert_no_nulls.sql
```

#### `seeds/`
CSV files for static/reference data.

**Example:**
```
seeds/
└── country_codes.csv
```

#### `macros/`
Reusable Jinja2 functions for complex logic.

**Example:**
```
macros/
└── generate_schema_name.sql
```

#### `analyses/`
Ad-hoc SQL queries that won't be part of the transformation.

#### `snapshots/`
Capture point-in-time changes to slowly changing dimensions.

---

## Common Commands

### Project Management
```bash
# Validate project and test connection
dbt debug

# Install package dependencies
dbt deps

# Clean build artifacts
dbt clean

# Check documentation
dbt docs generate
dbt docs serve
```

### Model Execution
```bash
# Run all models
dbt run

# Run specific model
dbt run --select model_name

# Run model and its dependents
dbt run --select +model_name+

# Run models with specific tag
dbt run --select tag:daily

# Run with full refresh (rebuild incremental models)
dbt run --full-refresh

# Dry run (compile without executing)
dbt compile
```

### Testing & Validation
```bash
# Run all tests
dbt test

# Test specific model
dbt test --select model_name

# Test with detailed output
dbt test --verbose

# Generate and view test results
dbt test --store-failures
```

### Development Workflow
```bash
# Run and test (typical dev cycle)
dbt run && dbt test

# Build with dependency resolution
dbt build

# Partial run for development
dbt run --select path:models/staging
```

### Advanced Operations
```bash
# Run with specific number of threads
dbt run --threads 8

# Run with environment variable
dbt run --vars '{"key": "value"}'

# Create snapshots
dbt snapshot

# Seed data
dbt seed

# Freshness check (for external sources)
dbt source freshness
```

---

## Key Features

### ✅ BigQuery Integration
- Direct connection to Google BigQuery for massive-scale data processing
- Support for BigQuery-specific features (clustering, partitioning, etc.)
- Efficient query compilation and execution

### ✅ Containerized Architecture
- Docker image ensures consistent environment across dev/prod
- Easy deployment to any cloud or on-premise infrastructure
- Reproducible builds with version-locked dependencies

### ✅ Automated CI/CD Pipeline
- Google Cloud Build triggers on every push
- Automatic image building and testing
- Seamless deployment to Cloud Run
- No manual deployment steps required

### ✅ Secure Authentication
- Service account-based authentication (more secure than password)
- Environment variable support for credentials
- No hardcoded secrets in version control

### ✅ Parallel Execution
- 4-thread default configuration for concurrent model execution
- Reduces overall execution time significantly
- Configurable based on resource availability

### ✅ Modular Design
- Standard dbt directory structure for clarity
- Separation of concerns (staging, marts, tests, etc.)
- Easy to scale and maintain

### ✅ Production-Ready
- Error handling and retry logic built-in
- Comprehensive logging for debugging
- Cloud Run Jobs handle scheduling and monitoring

---

## Architecture

### Data Flow
```
Raw Data in BigQuery
        ↓
    [dbt Models]
        ├─ Staging (clean, standardize)
        ├─ Intermediate (business logic)
        └─ Marts (final analytics tables)
        ↓
Transformed Data in BigQuery
        ↓
[BI Tools / Analytics / Reports]
```

### System Architecture
```
GitHub Repository
        ↓
Cloud Build (CI/CD)
        ├─ Build Docker Image
        ├─ Push to Artifact Registry
        └─ Deploy to Cloud Run
        ↓
Cloud Run Job
        ├─ Pulls Docker Image
        ├─ Runs dbt Commands
        └─ Writes Results to BigQuery
        ↓
Cloud Logging (Monitoring & Debugging)
```

### Component Interaction
```
┌─────────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   BigQuery   │ ← →│  dbt (via    │ ← →│Cloud Run Job │   │
│  │  Database    │    │Cloud Build)  │    │ (Execution)  │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│         ▲                                         ▲           │
│         │                                         │           │
│         └─────────── Cloud Logging ──────────────┘           │
│                      (Monitoring)                             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
        ▲
        │
        │ (git push)
        │
    GitHub Repository
```

---

## Deployment Pipeline

### Development → Production Flow

#### 1. Local Development
```bash
# Clone repo
git clone <repo-url>

# Create feature branch
git checkout -b feature/new-model

# Make changes to dbt models/tests
# Test locally
dbt run && dbt test

# Commit changes
git add .
git commit -m "Add new customer model"
```

#### 2. Push & Trigger Cloud Build
```bash
# Push to GitHub
git push origin feature/new-model

# Cloud Build automatically:
# 1. Clones repository
# 2. Builds Docker image
# 3. Runs tests in container
# 4. Pushes image to Artifact Registry
```

#### 3. Create Pull Request
- Create PR for code review
- Verify Cloud Build checks pass
- Request reviewers

#### 4. Merge to Main
- After approval, merge to main branch
- Cloud Build triggers again
- Image deployed to Cloud Run

#### 5. Production Execution
```bash
# View deployed job
gcloud run jobs describe dbt-job

# Manually trigger (or scheduled)
gcloud run jobs execute dbt-job

# View logs
gcloud run jobs log dbt-job
```

### Scheduling

#### Option 1: Cloud Scheduler
```bash
gcloud scheduler jobs create app-engine daily-dbt \
  --location=us-central1 \
  --schedule="0 2 * * *" \
  --http-method=POST \
  --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/PROJECT_ID/jobs/dbt-job:run"
```

#### Option 2: Cloud Workflows
Create a workflow to orchestrate dbt job execution and dependencies.

---

## Next Steps

### Phase 1: Setup (Current)
- [x] Clone repository
- [x] Understand project structure
- [ ] Update `profiles.yml` with your GCP credentials
- [ ] Test local connection (`dbt debug`)
- [ ] Run initial `dbt run` and `dbt test`

### Phase 2: Development
- [ ] Create staging models in `models/staging/`
- [ ] Define tests in `tests/`
- [ ] Document models in `schema.yml`
- [ ] Create marts/analytics models in `models/marts/`
- [ ] Test models locally

### Phase 3: Production Deployment
- [ ] Update `cloudbuild.yaml` with your project ID
- [ ] Connect GitHub to Cloud Build
- [ ] Test deployment pipeline
- [ ] Set up Cloud Scheduler for scheduling
- [ ] Monitor logs and performance

### Phase 4: Enhancement
- [ ] Add dbt packages for common utilities
- [ ] Implement data quality frameworks (Great Expectations, etc.)
- [ ] Create documentation and lineage
- [ ] Set up alerts for failed jobs
- [ ] Optimize query performance

---

## Troubleshooting

### Connection Issues

#### Problem: "Could not find service account JSON"
**Solution:**
```bash
# Verify file exists
ls -la /path/to/service-account.json

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Test connection
dbt debug
```

#### Problem: "BigQuery quota exceeded"
**Solution:**
- Reduce `threads` in `profiles.yml` (e.g., from 4 to 2)
- Check BigQuery admin for active queries
- Break large models into smaller incremental models

### Build Issues

#### Problem: "Docker build fails"
**Solution:**
```bash
# Clean build
docker build --no-cache -t dbt-runner .

# Check Docker daemon
docker ps

# View detailed output
docker build -t dbt-runner . 2>&1 | tail -50
```

#### Problem: "Cloud Build fails"
**Solution:**
1. Check Cloud Build logs: Cloud Console → Cloud Build → History
2. Verify service account permissions
3. Check Dockerfile syntax: `docker build -t test .` locally
4. Verify cloudbuild.yaml has correct project IDs

### dbt Issues

#### Problem: "dbt: command not found"
**Solution:**
```bash
# Reinstall dbt
pip install --upgrade dbt-bigquery==1.11.1

# Verify installation
dbt --version
```

#### Problem: "Model does not exist" error
**Solution:**
```bash
# Check model file location
ls models/

# Verify model name matches SQL filename
# models/my_model.sql should be referenced as `my_model` in dbt

# Rebuild
dbt clean && dbt run
```

#### Problem: "Circular dependency detected"
**Solution:**
- Review model dependencies in `schema.yml`
- Check `ref()` statements for circular references
- Break circular dependency by creating intermediate model

### Performance Issues

#### Problem: Models run slowly
**Solution:**
1. Increase `threads` in `profiles.yml` (max 8-10)
2. Enable BigQuery result caching (default)
3. Add clustering to large tables
4. Use incremental models for large datasets
5. Check BigQuery slot utilization

#### Problem: High BigQuery costs
**Solution:**
```bash
# Monitor query costs
# Use EXPLAIN in dbt to see query complexity

# Optimize:
dbt run --select tag:expensive --verbose

# Switch to incremental models
# Use dbt snapshots instead of full refreshes
# Partition large tables
```

### Git/GitHub Issues

#### Problem: "Permission denied" when pushing
**Solution:**
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to GitHub (Settings → SSH Keys)
cat ~/.ssh/id_ed25519.pub

# Test connection
ssh -T git@github.com
```

#### Problem: Cloud Build not triggering on push
**Solution:**
1. Verify GitHub repo connected in Cloud Build
2. Check branch name in Cloud Build trigger (matches main)
3. Verify trigger is enabled
4. Check CloudBuild service account has permissions

---

## Resources

### Official Documentation
- [dbt Documentation](https://docs.getdbt.com/)
- [dbt BigQuery Docs](https://docs.getdbt.com/reference/warehouse-setups/bigquery-setup)
- [Google Cloud Build](https://cloud.google.com/build/docs)
- [Google Cloud Run](https://cloud.google.com/run/docs)

### Community
- [dbt Community Discourse](https://discourse.getdbt.com/)
- [dbt Community Slack](https://community.getdbt.com/)
- [dbt GitHub Repository](https://github.com/dbt-labs/dbt-core)

### Best Practices
- [dbt Style Guide](https://github.com/dbt-labs/corp/blob/main/dbt_style_guide.md)
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)
- [BigQuery Best Practices](https://cloud.google.com/bigquery/docs/best-practices)

---

## Document Version
- **Created:** 2026-09-06
- **Last Updated:** 2026-09-06
- **Version:** 1.0.0
- **Author:** Documentation Team

---

## Appendix: Quick Reference

### Environment Variables
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
DBT_PROFILES_DIR=~/.dbt
DBT_TARGET=dev
```

### File Permissions (Linux/Mac)
```bash
# Service account JSON should be read-only
chmod 400 service-account.json

# Make shell scripts executable
chmod +x scripts/*.sh
```

### GCP Service Account Permissions
Minimum required IAM roles:
- `roles/bigquery.dataEditor` — Read/write BigQuery datasets
- `roles/bigquery.jobUser` — Run queries
- `roles/viewer` — Basic viewing permissions

### BigQuery Dataset Permissions
- Query data
- Create/modify tables and views
- Create temporary tables (for query execution)

---

