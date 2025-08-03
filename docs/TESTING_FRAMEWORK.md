# PanelMerge Testing Framework

## Overview

The PanelMerge application includes a comprehensive testing framework built with pytest and unittest. This framework provides thorough test coverage across unit tests, integration tests, and end-to-end workflows.

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── unit/                       # Unit tests
│   ├── test_models.py         # Database model tests
│   ├── test_database.py       # Comprehensive database operation tests
│   ├── test_database_migrations.py # Database migration and schema tests
│   ├── test_auth.py           # Authentication tests
│   ├── test_api.py            # API endpoint tests
│   ├── test_cache.py          # Caching functionality tests
│   └── test_file_upload.py    # File upload tests
├── integration/               # Integration tests
│   ├── test_workflows.py      # End-to-end workflow tests
│   └── test_database_integration.py # Database integration tests
└── fixtures/                  # Test data and utilities
    └── test_factories.py      # Factory classes for test data
```

## Features

### ✅ Comprehensive Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: Full workflow testing
- **API Tests**: Complete API endpoint coverage
- **Database Tests**: CRUD operations, data integrity, and schema validation
- **Migration Tests**: Database schema evolution and migration testing
- **Security Tests**: Authentication and authorization
- **Performance Tests**: Load and response time testing
- **File Upload Tests**: Upload validation and processing

### ✅ Test Markers and Organization
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests  
- `@pytest.mark.api` - API tests
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.database` - Database tests
- `@pytest.mark.cache` - Cache tests
- `@pytest.mark.security` - Security tests
- `@pytest.mark.slow` - Performance tests
- `@pytest.mark.file_upload` - File upload tests

### ✅ Advanced Testing Features
- **Factory Classes**: Automated test data generation with Factory Boy
- **Mock Objects**: Redis, API, and database mocking
- **Fixtures**: Reusable test components
- **Coverage Reporting**: HTML and terminal coverage reports
- **CI/CD Integration**: GitHub Actions workflow
- **Security Testing**: Bandit and Safety integration

## Quick Start

### Install Test Dependencies

```bash
# Install all testing dependencies
python run_tests.py --install-deps

# Or install manually
pip install pytest pytest-flask pytest-cov pytest-mock pytest-html coverage factory-boy freezegun responses
```

### Set Up Test Environment

```bash
# Set up test directories and configuration
python run_tests.py --setup
```

### Run Tests

```bash
# Run all tests
python run_tests.py

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration

# Run tests with coverage
python run_tests.py --coverage --html

# Run tests with specific markers
python run_tests.py --markers unit database
python run_tests.py --markers api security

# Generate comprehensive report
python run_tests.py --report
```

### Alternative pytest commands

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run tests matching pattern
pytest -k "test_user"

# Run tests with specific markers
pytest -m "unit and database"

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Test Configuration

### pytest.ini
The `pytest.ini` file contains:
- Test discovery settings
- Coverage configuration
- Marker definitions
- Warning filters

### conftest.py
Shared fixtures include:
- Application factory with test configuration
- Database session management
- Sample user and admin creation
- Mock Redis and cache objects
- File upload test data
- API authentication helpers

## Test Categories

### Unit Tests

#### Models (test_models.py)
- User model creation and validation
- Password hashing and verification
- Panel and Gene model relationships
- Admin message functionality
- Database constraints and uniqueness

#### Database Operations (test_database.py)
- **Schema Integrity**: Table structure and constraint validation
- **CRUD Operations**: Create, Read, Update, Delete operations
- **Data Integrity**: Unique constraints, foreign keys, data types
- **Transaction Handling**: Commit, rollback, nested transactions
- **Relationship Testing**: Model relationships and cascading
- **Performance Testing**: Bulk operations and query optimization
- **Security Testing**: SQL injection prevention, password hashing
- **Stress Testing**: Large dataset handling, concurrent access

#### Database Migrations (test_database_migrations.py)
- **Schema Structure**: Current database schema validation
- **Migration Compatibility**: Forward and backward compatibility
- **Data Type Validation**: Field types and constraints
- **Index Validation**: Critical index existence and effectiveness
- **Version Tracking**: Schema evolution and versioning
- **Rollback Testing**: Migration rollback scenarios

#### Authentication (test_auth.py)
- Login/logout workflows
- User registration
- Password validation
- Session security
- Admin access control
- CSRF protection

#### API (test_api.py)
- All API endpoint functionality
- Request/response validation
- Authentication and authorization
- Error handling
- Rate limiting
- Swagger documentation

#### Cache (test_cache.py)
- Redis connection and operations
- Flask-Caching integration
- Cache performance
- Error handling and fallbacks
- Cache invalidation

#### File Upload (test_file_upload.py)
- File validation (CSV, Excel)
- Upload processing
- Security scanning
- Error handling
- Storage management

### Integration Tests

#### Workflows (test_workflows.py)
- Complete user registration → login → usage → logout
- Admin user management workflows
- API authentication and usage flows
- Panel discovery and exploration
- File upload and processing
- Cache integration with real data
- Database transaction handling
- Performance with large datasets

#### Database Integration (test_database_integration.py)
- **Workflow Testing**: Complete database workflows (registration, login, downloads)
- **Concurrency Testing**: Concurrent database operations and deadlock prevention
- **Performance Integration**: Large-scale operations and real-world scenarios
- **Backup/Recovery**: Data export/import cycles and consistency validation
- **Complex Relationships**: Multi-table operations and relationship queries

## Test Data Management

### Factory Classes
Using Factory Boy for generating test data:

```python
# Create test user
user = UserFactory(username='testuser')

# Create admin user
admin = AdminUserFactory()

# Create panel with genes
panel = PanelFactory()
genes = GeneFactory.create_batch(5, panel_id=panel.panel_id)

# Create admin message
message = AdminMessageFactory(created_by=admin.id)
```

### Test Data Utilities
- CSV and Excel test data generation
- Large dataset creation for performance testing
- Malicious input generation for security testing
- Mock API responses
- Redis client simulation

## CI/CD Integration

### GitHub Actions Workflow
The testing workflow includes:

1. **Multi-Python Testing** (Python 3.9, 3.10, 3.11)
2. **Unit and Integration Tests**
3. **Security Testing** (Bandit, Safety)
4. **Performance Testing**
5. **API Testing**
6. **Coverage Reporting** (Codecov integration)
7. **Artifact Upload** (Test reports, coverage)

### Test Matrix
- **Python Versions**: 3.9, 3.10, 3.11
- **Test Types**: Unit, Integration, Security, Performance, API
- **Services**: Redis for cache testing
- **Reports**: Coverage, Security, Performance

## Performance Testing

### Load Testing
- Large dataset handling (1000+ panels/genes)
- Concurrent request simulation
- Response time validation
- Memory usage monitoring

### Benchmarks
- API response times < 5 seconds
- Database operations < 1 second
- Cache operations < 100ms
- File processing based on size

## Security Testing

### Test Coverage
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- File upload security
- Authentication bypass attempts
- Session security

### Security Tools
- **Bandit**: Static security analysis
- **Safety**: Dependency vulnerability scanning
- **Custom Tests**: Application-specific security validation

## Coverage Goals

- **Overall Coverage**: > 90%
- **Critical Components**: > 95%
  - Authentication system
  - API endpoints
  - File upload processing
  - Database models
- **Integration Coverage**: > 80%

## Best Practices

### Writing Tests
1. **Descriptive Names**: Use clear, descriptive test names
2. **Single Responsibility**: One test per functionality
3. **Arrange-Act-Assert**: Clear test structure
4. **Mock External Dependencies**: Avoid external service calls
5. **Test Edge Cases**: Include error conditions and boundary cases

### Test Organization
1. **Use Markers**: Tag tests appropriately
2. **Group Related Tests**: Use test classes
3. **Shared Fixtures**: Reuse common setup
4. **Clean Isolation**: Each test should be independent

### Performance Considerations
1. **Fast Unit Tests**: < 1 second each
2. **Database Rollback**: Clean state between tests
3. **Mock Heavy Operations**: Cache, API calls, file operations
4. **Parallel Execution**: Use pytest-xdist for speed

## Troubleshooting

### Common Issues

1. **Database Lock Errors**
   ```bash
   # Solution: Ensure proper test isolation
   pytest --forked
   ```

2. **Redis Connection Errors**
   ```bash
   # Solution: Use mock Redis for unit tests
   pytest -m "not redis"
   ```

3. **Import Errors**
   ```bash
   # Solution: Check PYTHONPATH
   export PYTHONPATH=$PWD:$PYTHONPATH
   ```

4. **Coverage Not Working**
   ```bash
   # Solution: Install coverage properly
   pip install coverage pytest-cov
   ```

### Debug Mode
```bash
# Run tests with debugger
pytest --pdb

# Run with print statements
pytest -s

# Run single test with verbose output
pytest tests/unit/test_models.py::TestUserModel::test_user_creation -v -s
```

## Future Enhancements

### Planned Additions
- **Load Testing**: Locust integration for realistic load testing
- **Visual Testing**: Screenshot comparison for UI components  
- **Contract Testing**: API contract validation
- **Mutation Testing**: Code quality validation with mutmut
- **Property-Based Testing**: Hypothesis integration for edge case discovery

### Integration Opportunities
- **Docker Testing**: Containerized test environments
- **Database Testing**: Multi-database compatibility
- **Browser Testing**: Selenium integration for E2E testing
- **Monitoring Integration**: Test result monitoring and alerting

## Contributing

When adding new features:

1. **Write Tests First**: Follow TDD approach
2. **Add Appropriate Markers**: Tag tests correctly
3. **Update Documentation**: Keep this guide current
4. **Check Coverage**: Maintain coverage goals
5. **Run Full Suite**: Ensure no regressions

---

## Commands Reference

```bash
# Basic test commands
python run_tests.py                    # Run all tests
python run_tests.py --type unit        # Unit tests only
python run_tests.py --type integration # Integration tests only
python run_tests.py --type database    # Database tests only
python run_tests.py --coverage --html  # With HTML coverage report
python run_tests.py --report          # Generate comprehensive report

# Database-specific testing
python run_tests.py --database                    # All database tests
python run_tests.py --database-type unit          # Unit database tests
python run_tests.py --database-type integration   # Integration database tests
python run_tests.py --database-type migrations    # Migration tests
python run_tests.py --database-type performance   # Performance database tests

# Dedicated database test runner
python run_database_tests.py                      # All database tests
python run_database_tests.py --type unit          # Unit database tests
python run_database_tests.py --type migrations    # Migration tests
python run_database_tests.py --benchmark          # Performance benchmarks
python run_database_tests.py --schema             # Schema validation
python run_database_tests.py --stress             # Stress tests
python run_database_tests.py --report             # Comprehensive database report

# Marker-based testing  
python run_tests.py --markers unit database       # Unit + database tests
python run_tests.py --markers api security        # API + security tests
python run_tests.py --markers slow               # Performance tests

# Pattern-based testing
python run_tests.py --pattern "test_user"        # Tests matching pattern

# Setup and maintenance
python run_tests.py --setup           # Set up test environment
python run_tests.py --install-deps    # Install dependencies

# Direct pytest commands
pytest tests/unit/                    # Unit tests
pytest -m "unit and database"         # Marker combination
pytest -k "test_user"                 # Pattern matching
pytest tests/unit/test_database.py    # Specific database test file
pytest tests/unit/test_database_migrations.py::TestDatabaseSchema # Specific test class
pytest -m "database and not slow"     # Database tests excluding slow ones
python run_tests.py --type integration # Integration tests only
python run_tests.py --coverage --html  # With HTML coverage report
python run_tests.py --report          # Generate comprehensive report

# Marker-based testing  
python run_tests.py --markers unit database    # Unit + database tests
python run_tests.py --markers api security     # API + security tests
python run_tests.py --markers slow            # Performance tests

# Pattern-based testing
python run_tests.py --pattern "test_user"     # Tests matching pattern

# Setup and maintenance
python run_tests.py --setup           # Set up test environment
python run_tests.py --install-deps    # Install dependencies

# Direct pytest commands
pytest tests/unit/                    # Unit tests
pytest -m "unit and database"         # Marker combination
pytest -k "test_user"                 # Pattern matching
pytest --cov=app --cov-report=html    # Coverage report
pytest -v -x                          # Verbose, stop on failure
```

This comprehensive testing framework ensures the reliability, security, and performance of the PanelMerge application through automated testing at multiple levels.
