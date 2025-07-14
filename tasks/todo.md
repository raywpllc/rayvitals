# RayVitals Backend API Development Plan

## Overview
Starting with the backend API as the foundation, since all WordPress plugin functionality depends on it. This plan focuses on creating a minimal viable API that can perform basic website audits and provide simple testing capabilities.

## Development Tasks

### Phase 1: Core API Infrastructure (High Priority)
- [ ] Set up GitHub repository with initial backend API structure
- [ ] Create FastAPI project structure with basic configuration
- [ ] Set up Supabase database connection and basic schema
- [ ] Create basic website audit endpoints (POST /audit/start, GET /audit/status)

### Phase 2: Basic Audit Capabilities (Medium Priority)
- [ ] Implement simple security scan (SSL check, basic headers)
- [ ] Add basic performance testing (simple page load metrics)
- [ ] Create simple AI integration for basic website analysis summary
- [ ] Set up async job processing with Celery + Redis

### Phase 3: Testing & Development Tools (Low Priority)
- [ ] Create API testing suite and simple web interface for testing
- [ ] Add Docker setup for local development

## Quick Testing Strategy

Once basic endpoints are established, we'll create:
1. **Simple HTTP client tests** using pytest + requests
2. **Basic web interface** (single HTML page) to trigger scans and view results
3. **Postman/curl examples** for manual API testing
4. **Health check endpoints** to verify all services are working

## Technology Stack (From Spec)
- **Backend**: FastAPI (Python 3.11+)
- **Database**: Supabase (PostgreSQL)
- **Queue**: Celery + Redis
- **AI**: Google Gemini API
- **External APIs**: Various audit services (SSL Labs, PageSpeed, etc.)

## Success Criteria for MVP
- API can receive a website URL and return an audit ID
- Basic security and performance checks complete successfully
- Results stored in Supabase and retrievable via API
- Simple AI summary generated from audit results
- All endpoints documented and testable

## Progress Update

### ✅ Completed Tasks
- [x] Set up GitHub repository with initial backend API structure
- [x] Create FastAPI project structure with basic configuration
- [x] Create basic website audit endpoints (POST /audit/start, GET /audit/status)
- [x] Implement simple security scan (SSL check, basic headers)
- [x] Add basic performance testing (simple page load metrics)
- [x] Create simple AI integration for basic website analysis summary
- [x] Create API testing suite and simple web interface for testing
- [x] Add Docker setup for local development

### ⏳ Remaining Tasks
- [ ] Set up Supabase database connection and basic schema
- [ ] Set up async job processing with Celery + Redis

## Review

### Changes Made
1. **Created comprehensive FastAPI backend structure** with modular design
2. **Implemented custom security and performance scanning** following the API sources analysis strategy
3. **Added Google Gemini AI integration** for business intelligence analysis
4. **Built complete audit workflow** with async processing support
5. **Created Docker setup** for easy local development
6. **Added comprehensive testing interface** (test_interface.html) for manual API testing
7. **Set up proper database models** for Supabase integration
8. **Implemented fallback strategies** for all external dependencies

### Key Features Implemented
- **Security Analysis**: Custom SSL, headers, and vulnerability scanning
- **Performance Testing**: Load time measurement, HTTP response analysis
- **AI Business Intelligence**: Gemini-powered analysis with fallback summaries
- **Async Processing**: Background task architecture (ready for Celery)
- **Health Monitoring**: Detailed health checks for all services
- **Testing Interface**: Simple web UI for testing all endpoints

### Architecture Decisions
- **Custom implementations over external APIs** for core functionality (security, performance)
- **Modular service architecture** for easy extension and testing
- **Comprehensive error handling** with structured logging
- **Docker-first development** for consistent environments
- **Database-agnostic design** with Supabase as primary choice

### Next Steps
To complete the MVP, you'll need to:
1. **Set up Supabase project** and configure database connection
2. **Add Celery worker setup** for production async processing
3. **Create GitHub repository** (needs GitHub CLI authentication)
4. **Test full workflow** with real database

The backend is now ready for testing and can be deployed to Digital Ocean or Vultr once the remaining database setup is complete.

---

# Database URL Duplication Fix Plan

## Problem Analysis
- DigitalOcean has duplicate DATABASE_URL environment variables
- One encrypted DATABASE_URL that overrides app-level variable
- Another DATABASE_URL with value `${rayvitals-postgres.DATABASE_URL}`
- App-level DATABASE_URL is being overridden (marked as overridden)
- This can cause connection conflicts and unpredictable behavior

## Current Database URL Usage
- Used in `/app/core/config.py` for settings configuration
- Used in `/app/core/database.py` for SQLAlchemy async engine creation
- Critical for Supabase PostgreSQL connection
- Required for audit storage, user management, and result storage

## Todo Items

### Investigation Tasks
- [ ] Verify which DATABASE_URL is currently being used by the application
- [ ] Check if the managed database service `rayvitals-postgres` is the correct source
- [ ] Determine if both variables are causing conflicts

### Resolution Tasks
- [ ] Remove the duplicate DATABASE_URL environment variable from DigitalOcean
- [ ] Keep only the managed database reference: `${rayvitals-postgres.DATABASE_URL}`
- [ ] Test database connectivity after cleanup
- [ ] Verify application startup and database operations work correctly

### Verification Tasks
- [ ] Test the application deployment after cleanup
- [ ] Verify audit functionality works with single DATABASE_URL
- [ ] Check logs for any database connection errors
- [ ] Confirm no regression in database-dependent features

### Documentation Tasks
- [ ] Update deployment documentation if needed
- [ ] Add notes about proper DATABASE_URL configuration for future reference

## Next Steps
1. Remove the duplicate encrypted DATABASE_URL variable
2. Keep the managed database reference
3. Test deployment and functionality
4. Monitor for any issues

---

# DigitalOcean Database Connection Troubleshooting

## Plan
1. [x] Examine current codebase for database configuration
2. [ ] Check DigitalOcean app configuration and environment variables
3. [ ] Verify database connection setup in the application
4. [ ] Check DigitalOcean database cluster status and connection details
5. [ ] Identify and fix database connection issues

## Progress
- ✅ Found database configuration files and analyzed structure
- Starting DigitalOcean configuration analysis

## Database Configuration Analysis Results

### Found Database Configuration Files:

1. **Primary Configuration Files:**
   - `/Users/arosenkoetter/Sites/RavVitals/rayvitals-backend/app/core/config.py` - Main settings configuration
   - `/Users/arosenkoetter/Sites/RavVitals/rayvitals-backend/app/core/database.py` - Database connection management
   - `/Users/arosenkoetter/Sites/RavVitals/rayvitals-backend/.env` - Environment variables
   - `/Users/arosenkoetter/Sites/RavVitals/rayvitals-backend/.env.example` - Example configuration

2. **Model Files:**
   - `/Users/arosenkoetter/Sites/RavVitals/rayvitals-backend/app/models/audit.py` - Audit data models
   - `/Users/arosenkoetter/Sites/RavVitals/rayvitals-backend/app/models/user.py` - User and site models

3. **Connection Testing:**
   - `/Users/arosenkoetter/Sites/RavVitals/rayvitals-backend/test_db_connection.py` - Database connection test script

### Database Configuration Details:

#### Current DATABASE_URL Configuration:
- **Live Connection String:** `postgresql+asyncpg://doadmin:[REDACTED]@rayvitals-postgres-do-user-23911477-0.k.db.ondigitalocean.com:25060/defaultdb?sslmode=require`
- **Database Type:** PostgreSQL with AsyncPG driver
- **SSL Mode:** Required
- **Host:** DigitalOcean managed database cluster

#### Key Configuration Settings:
- Uses `pydantic_settings.BaseSettings` for configuration management
- Database URL loaded from environment variables
- Supports both Supabase and direct PostgreSQL connections
- Async SQLAlchemy engine with connection pooling
- Automatic database initialization on startup

#### Database Schema:
- **audit_requests:** Main audit tracking table
- **audit_results:** Detailed audit results by category
- **audit_metrics:** Performance and security metrics
- **site_registrations:** WordPress site management
- **api_keys:** API key management

#### Connection Management:
- Lazy initialization of database engine
- Connection pooling with pre-ping and recycle settings
- Comprehensive error handling and logging
- Graceful degradation if database unavailable

### Potential Issues Identified:

1. **Environment Variable Conflicts:** The todo mentions duplicate DATABASE_URL variables in DigitalOcean
2. **Supabase Integration:** Code has both Supabase and direct PostgreSQL support but Supabase client is disabled
3. **Connection String Format:** Using `postgresql+asyncpg://` format for async connections

### Next Steps:
- Check DigitalOcean environment variable configuration
- Verify which DATABASE_URL is being used
- Test database connectivity
- Resolve any duplicate environment variables

## Review
(To be completed after fixing the issues)

---

## Review Section
(To be completed after implementation)