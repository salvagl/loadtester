#!/bin/bash

# LoadTester Setup Script
# This script sets up the complete LoadTester environment

set -e  # Exit on any error

echo "🚀 LoadTester Setup Script"
echo "=========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check available space
    available_space=$(df . | tail -1 | awk '{print $4}')
    if [ $available_space -lt 10485760 ]; then  # 10GB in KB
        print_warning "Less than 10GB free space available. LoadTester may not work properly."
    fi
    
    print_success "Prerequisites check completed"
}

# Create directory structure
create_directories() {
    print_status "Creating directory structure..."
    
    # Create main directories
    mkdir -p backend/app/{domain/{entities,interfaces,services},infrastructure/{database,repositories,external,config},presentation/{api/v1/endpoints,middleware},shared/{exceptions,utils,constants},tests/{unit,integration}}
    mkdir -p frontend/components
    mkdir -p k6/{scripts/generated,results/generated}
    mkdir -p shared/{database,data/{uploads,mocked},reports/generated}
    mkdir -p docs
    
    # Create .gitkeep files for empty directories
    touch shared/database/.gitkeep
    touch shared/data/uploads/.gitkeep
    touch shared/data/mocked/.gitkeep
    touch shared/reports/generated/.gitkeep
    touch k6/scripts/generated/.gitkeep
    touch k6/results/generated/.gitkeep
    
    print_success "Directory structure created"
}

# Create __init__.py files
create_init_files() {
    print_status "Creating Python __init__.py files..."
    
    # Backend __init__.py files
    echo '"""LoadTester Backend Application"""' > backend/app/__init__.py
    echo '"""Domain Layer"""' > backend/app/domain/__init__.py
    echo '"""Domain Entities"""' > backend/app/domain/entities/__init__.py
    echo '"""Domain Interfaces"""' > backend/app/domain/interfaces/__init__.py
    echo '"""Domain Services"""' > backend/app/domain/services/__init__.py
    echo '"""Infrastructure Layer"""' > backend/app/infrastructure/__init__.py
    echo '"""Database Infrastructure"""' > backend/app/infrastructure/database/__init__.py
    echo '"""Repository Implementations"""' > backend/app/infrastructure/repositories/__init__.py
    echo '"""External Services"""' > backend/app/infrastructure/external/__init__.py
    echo '"""Configuration"""' > backend/app/infrastructure/config/__init__.py
    echo '"""Presentation Layer"""' > backend/app/presentation/__init__.py
    echo '"""API Layer"""' > backend/app/presentation/api/__init__.py
    echo '"""API v1"""' > backend/app/presentation/api/v1/__init__.py
    echo '"""API Endpoints"""' > backend/app/presentation/api/v1/endpoints/__init__.py
    echo '"""Middleware"""' > backend/app/presentation/middleware/__init__.py
    echo '"""Shared Components"""' > backend/app/shared/__init__.py
    echo '"""Exceptions"""' > backend/app/shared/exceptions/__init__.py
    echo '"""Utilities"""' > backend/app/shared/utils/__init__.py
    echo '"""Constants"""' > backend/app/shared/constants/__init__.py
    echo '"""Tests"""' > backend/app/tests/__init__.py
    
    # Frontend __init__.py files
    echo '"""Streamlit Components"""' > frontend/components/__init__.py
    
    print_success "Python __init__.py files created"
}

# Setup environment configuration
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_warning "Created .env file from .env.example"
            print_warning "IMPORTANT: Please edit .env file and add your AI service API keys"
        else
            # Create basic .env file
            cat > .env << EOF
# LoadTester Environment Configuration
# Please configure your AI service API keys

# AI Services (at least one required)
GOOGLE_API_KEY=your_google_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Application Settings
APP_NAME=LoadTester
APP_VERSION=0.0.1
LOG_LEVEL=INFO
DEBUG=false

# Database
DATABASE_URL=sqlite:///data/loadtester.db

# Load Testing Configuration
DEGRADATION_RESPONSE_TIME_MULTIPLIER=5.0
DEGRADATION_ERROR_RATE_THRESHOLD=0.5
DEFAULT_TEST_DURATION=60
MAX_CONCURRENT_JOBS=1

# File Upload
MAX_FILE_SIZE=10485760
ALLOWED_FILE_EXTENSIONS=.csv,.json,.xlsx

# Paths
K6_SCRIPTS_PATH=/app/k6_scripts
K6_RESULTS_PATH=/app/k6_results
UPLOAD_PATH=/app/shared/data/uploads
REPORTS_PATH=/app/shared/reports/generated

# Security
SECRET_KEY=change-this-in-production-$(openssl rand -base64 32 2>/dev/null || echo "default-secret-key")

# Frontend
BACKEND_URL=http://backend:8000
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
EOF
            print_warning "Created basic .env file"
            print_warning "IMPORTANT: Please edit .env file and add your AI service API keys"
        fi
    else
        print_success "Environment file .env already exists"
    fi
}

# Validate environment
validate_environment() {
    print_status "Validating environment configuration..."
    
    if [ -f .env ]; then
        source .env
        
        # Check if at least one AI service is configured
        if [[ -z "$GOOGLE_API_KEY" || "$GOOGLE_API_KEY" == "your_google_gemini_api_key_here" ]] && \
           [[ -z "$ANTHROPIC_API_KEY" || "$ANTHROPIC_API_KEY" == "your_anthropic_api_key_here" ]] && \
           [[ -z "$OPENAI_API_KEY" || "$OPENAI_API_KEY" == "your_openai_api_key_here" ]]; then
            print_error "No AI service API keys configured in .env file"
            print_error "Please edit .env and add at least one API key:"
            print_error "  - GOOGLE_API_KEY (Google Gemini)"
            print_error "  - ANTHROPIC_API_KEY (Anthropic Claude)"
            print_error "  - OPENAI_API_KEY (OpenAI GPT)"
            return 1
        fi
        
        print_success "Environment validation passed"
    else
        print_error ".env file not found"
        return 1
    fi
}

# Build and start services
start_services() {
    print_status "Building and starting LoadTester services..."
    
    # Build and start services
    docker-compose up --build -d
    
    # Wait for services to be ready
    print_status "Waiting for services to start..."
    sleep 10
    
    # Check backend health
    max_attempts=30
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend service is healthy"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Backend service failed to start"
            print_error "Check logs with: docker-compose logs backend"
            return 1
        fi
        
        print_status "Waiting for backend... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    # Check frontend health
    max_attempts=30
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
            print_success "Frontend service is healthy"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Frontend service failed to start"
            print_error "Check logs with: docker-compose logs frontend"
            return 1
        fi
        
        print_status "Waiting for frontend... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    print_success "All services started successfully"
}

# Display final information
show_completion_info() {
    echo ""
    echo "🎉 LoadTester Setup Complete!"
    echo "============================="
    echo ""
    echo "Services are running at:"
    echo "  • Frontend (Streamlit UI): http://localhost:8501"
    echo "  • Backend (API):           http://localhost:8000"
    echo "  • API Documentation:       http://localhost:8000/docs"
    echo ""
    echo "Useful commands:"
    echo "  • View logs:        docker-compose logs -f"
    echo "  • Stop services:    docker-compose down"
    echo "  • Restart services: docker-compose restart"
    echo "  • View status:      docker-compose ps"
    echo ""
    echo "Next steps:"
    echo "  1. Open http://localhost:8501 in your browser"
    echo "  2. Upload your OpenAPI specification"
    echo "  3. Configure your load test"
    echo "  4. Run your first load test!"
    echo ""
    echo "For help and documentation:"
    echo "  • README.md - Getting started guide"
    echo "  • docs/API.md - API documentation"
    echo "  • docs/DEPLOYMENT.md - Deployment guide"
    echo "  • docs/DATA_FORMATS.md - Data format specifications"
    echo ""
}

# Main execution
main() {
    echo "Starting LoadTester setup process..."
    echo ""
    
    check_prerequisites || exit 1
    create_directories || exit 1
    create_init_files || exit 1
    setup_environment || exit 1
    
    # Ask user to configure API keys if needed
    if ! validate_environment; then
        echo ""
        print_warning "Please edit the .env file to add your AI service API keys, then run:"
        print_warning "  docker-compose up --build -d"
        echo ""
        print_warning "Or re-run this script after configuring the API keys."
        exit 1
    fi
    
    start_services || exit 1
    show_completion_info
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "LoadTester Setup Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --check-only   Only check prerequisites and environment"
        echo "  --no-start     Setup but don't start services"
        echo ""
        echo "This script will:"
        echo "  1. Check system prerequisites"
        echo "  2. Create directory structure"
        echo "  3. Setup environment configuration"
        echo "  4. Build and start LoadTester services"
        exit 0
        ;;
    --check-only)
        check_prerequisites
        validate_environment
        exit $?
        ;;
    --no-start)
        check_prerequisites || exit 1
        create_directories || exit 1
        create_init_files || exit 1
        setup_environment || exit 1
        validate_environment || exit 1
        print_success "Setup complete. Run 'docker-compose up --build -d' to start services."
        exit 0
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        print_error "Use --help for usage information"
        exit 1
        ;;
esac