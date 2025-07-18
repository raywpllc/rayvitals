# RayVitals Project Architecture

## System Overview
RayVitals is a WordPress website audit platform with two main components:

### 1. Backend API (rayvitals-backend/)
**Purpose**: Pure REST API service for website auditing
**Technology**: FastAPI (Python), PostgreSQL, DigitalOcean App Platform
**URL**: https://rayvitals-backend-xwq86.ondigitalocean.app
**API Sources**: api_sources_analysis.md

**Core Services**:
- **Audit Service** (`/app/services/audit_service.py`) - Main orchestrator
- **Security Scanner** (`/app/services/security_scanner.py`) - SSL, headers, vulnerabilities
- **Performance Scanner** (`/app/services/performance_scanner.py`) - Load times, metrics
- **AI Analyzer** (`/app/services/ai_analyzer.py`) - Gemini-powered business intelligence

**Database Schema**:
- `audit_requests` - Main audit tracking (scores, status, AI summaries)
- `audit_results` - Detailed findings by category (security, performance, SEO)
- `audit_metrics` - Performance data (Core Web Vitals, timings)

**Key Endpoints**:
- `POST /api/v1/audit/start` - Start new audit
- `GET /api/v1/audit/status/{id}` - Poll audit progress
- `GET /api/v1/audit/results/{id}` - Get complete results

### 2. WordPress Plugin (planned)
**Purpose**: User interface and WordPress integration
**Technology**: PHP, WordPress Admin UI
**Integration**: Calls backend API, displays results in WordPress

**Planned Flow**:
1. Plugin UI → POST to API to start audit
2. Plugin polls API for status updates
3. Plugin displays results in WordPress admin

## Current Status
- ✅ Backend API fully functional with database storage
- ✅ All audit services working (security, performance, SEO, AI)
- ✅ Deployed on DigitalOcean with PostgreSQL database
- 🚧 WordPress plugin development pending

## Development Workflow

1. First think through the problem, read the codebase for relevant files, and write a plan to tasks/todo.md.
2. The plan should have a list of todo items that you can check off as you complete them
3. Before you begin working, check in with me and I will verify the plan.
4. Then, begin working on the todo items, marking them as complete as you go.
5. Please every step of the way just give me a high level explanation of what changes you made
6. Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity.
7. Finally, add a review section to the [todo.md](http://todo.md/) file with a summary of the changes you made and any other relevant information.