# Multi-Tenant Grounded CV Generator

A production-ready, multi-tenant SaaS application for AI-powered CV generation with evidence-based matching from user-specific CV knowledge bases.

## 🎯 Overview

This system transforms the original single-user CV generator into a scalable, multi-tenant application where each user has their own isolated CV collection and can generate tailored CVs from their entire CV history.

## 🏗️ Architecture

### Multi-Tenant Data Isolation

```
User A                    User B                    User C
├── cv_chunks_user_a     ├── cv_chunks_user_b     ├── cv_chunks_user_c
├── CV 1 (10 chunks)     ├── CV 1 (15 chunks)     ├── CV 1 (8 chunks)
├── CV 2 (12 chunks)     ├── CV 2 (9 chunks)      ├── CV 2 (14 chunks)
└── CV 3 (8 chunks)      └── CV 3 (11 chunks)     └── CV 3 (12 chunks)
```

### System Components

1. **Authentication Layer** (`auth/supabase_auth.py`)
   - Supabase-based user authentication
   - Session management
   - User registration and login

2. **User-Specific Data Layer** (`utils/user_qdrant_client.py`)
   - Isolated Qdrant collections per user
   - User-specific CV storage and retrieval
   - Cross-CV knowledge base queries

3. **Multi-Tenant CV Processing** (`modules/cv_ingestion/user_cv_processor.py`)
   - User-specific CV ingestion
   - Isolated embedding storage
   - User collection management

4. **Web Interface** (`web_app.py`)
   - Authentication-protected interface
   - User-specific CV dashboard
   - Knowledge base CV generation

## 🚀 Key Features

### 🔐 Secure Multi-Tenancy
- **Complete Data Isolation**: Each user gets their own Qdrant collection
- **Supabase Authentication**: Enterprise-grade user management
- **Session Security**: Secure session handling with automatic expiration

### 🧠 Knowledge Base CV Generation
- **Multi-CV Intelligence**: Generate CVs using experience from ALL user's CVs
- **Source Attribution**: Track which CV contributed each piece of experience
- **Evidence-Based**: Every claim in generated CV is backed by actual CV content

### 📊 User Dashboard
- **CV Collection Overview**: See all uploaded CVs with statistics
- **Smart Generation**: Automatic selection of best experience across CV history
- **Download Options**: Generated CV, evidence report, and source attribution

### 🎨 Professional Interface
- **Apple-Style Design**: Clean, modern interface
- **Responsive Layout**: Works on desktop and mobile
- **Real-Time Processing**: Progress indicators and status updates

## 📋 Quick Start

### Prerequisites
- Python 3.11+
- Supabase account and project
- OpenAI API key
- Qdrant server (local or cloud)

### Installation

1. **Clone and Setup**:
```bash
git clone <repository-url>
cd grounded-cv-generator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment Configuration**:
```bash
cp env.example .env
# Edit .env with your API keys and configuration
```

3. **Run Application**:
```bash
streamlit run web_app.py
```

## 🔧 Configuration

### Environment Variables

```env
# Authentication
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key

# AI Services
OPENAI_API_KEY=your-openai-api-key

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-api-key

# Application
ENVIRONMENT=development
ORCHESTRATOR=langchain
```

### Supabase Setup

1. Create a new Supabase project
2. Enable email authentication
3. Configure email templates (optional)
4. Set up custom user profiles (optional):

```sql
CREATE TABLE public.user_profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT,
  full_name TEXT,
  subscription_tier TEXT DEFAULT 'free',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🎮 Usage

### User Registration & Login

1. **New Users**: Click "Register" tab and create account
2. **Email Verification**: Check email for verification link (if enabled)
3. **Login**: Use email and password to access the system

### CV Management

1. **First CV**: Upload your first CV to start building knowledge base
2. **Additional CVs**: Add more CVs to expand your experience database
3. **View Collection**: See all your CVs with statistics and previews

### CV Generation

1. **Job Description**: Paste the target job description
2. **Generate**: Click "Generate Grounded CV" button
3. **Review Results**: See matches, sources, and generated CV
4. **Download**: Get CV, evidence report, and source attribution

## 🏢 Production Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for comprehensive production deployment instructions including:

- Linode server setup
- SSL certificate configuration
- Nginx reverse proxy
- Systemd service configuration
- Security hardening
- Monitoring and backup strategies

## 🔒 Security Features

### Data Isolation
- **User Collections**: Each user gets `cv_chunks_user_{user_id}` collection
- **No Cross-User Access**: Impossible for users to access other users' data
- **Secure Queries**: All database queries filtered by user ID

### Authentication Security
- **JWT Tokens**: Secure session management with Supabase
- **Password Hashing**: Supabase handles secure password storage
- **Session Expiration**: Automatic logout after inactivity

### Application Security
- **Input Validation**: All user inputs validated and sanitized
- **HTTPS Enforcement**: SSL/TLS encryption in production
- **Environment Variables**: Sensitive data stored securely

## 📊 Monitoring & Analytics

### User Metrics
- CV collection size per user
- Generation frequency
- Success/failure rates
- Performance metrics

### System Metrics
- Database performance
- API response times
- Error rates
- Resource utilization

## 🔧 API Reference

### Core Classes

#### `GroundedCVGenerator(user_id: str)`
Main orchestrator with user-specific initialization.

```python
generator = GroundedCVGenerator(user_id="user-123")
cv_stats = generator.get_user_cv_collection(user_id)
result = generator.generate_cv_from_knowledge_base(user_id, job_description)
```

#### `UserQdrantClient(user_id: str)`
User-specific Qdrant operations.

```python
client = UserQdrantClient(user_id="user-123")
cvs = client.get_user_cvs()
matches = client.query_across_all_user_cvs(query_embedding, limit=20)
```

#### `UserCVProcessor(user_id: str)`
User-specific CV processing.

```python
processor = UserCVProcessor(user_id="user-123")
result = processor.process_cv(file_path, cv_id)
stats = processor.get_user_cv_stats()
```

#### `StreamlitAuth()`
Authentication management for Streamlit.

```python
auth = StreamlitAuth()
user_id = auth.require_authentication()
auth.show_user_info()
```

## 🧪 Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### User Acceptance Tests
```bash
pytest tests/e2e/
```

## 🚀 Scaling Considerations

### Horizontal Scaling
- **Load Balancing**: Multiple Streamlit instances behind load balancer
- **Database Sharding**: Distribute user collections across Qdrant instances
- **Caching Layer**: Redis for frequently accessed data

### Vertical Scaling
- **Resource Monitoring**: Track CPU, memory, and storage usage
- **Database Optimization**: Index optimization and query tuning
- **Connection Pooling**: Efficient database connection management

## 🛠️ Development

### Project Structure
```
├── auth/                    # Authentication modules
│   └── supabase_auth.py    # Supabase authentication
├── utils/                   # Utility modules
│   ├── user_qdrant_client.py  # User-specific Qdrant client
│   ├── embeddings.py       # Embedding generation
│   └── cv_parser.py        # CV parsing utilities
├── modules/                 # Core processing modules
│   └── cv_ingestion/
│       ├── cv_processor.py      # Original processor
│       └── user_cv_processor.py # User-specific processor
├── agents/                  # AI agents
├── web_app.py              # Main Streamlit application
├── main.py                 # Core orchestrator
└── requirements.txt        # Dependencies
```

### Adding New Features

1. **User-Specific Features**: Always include `user_id` parameter
2. **Data Isolation**: Ensure all database operations are user-filtered
3. **Authentication**: Protect all endpoints with authentication
4. **Testing**: Add tests for multi-tenant scenarios

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Check Supabase configuration
   - Verify environment variables
   - Review Supabase project settings

2. **Data Isolation Issues**:
   - Verify user_id is passed correctly
   - Check collection naming conventions
   - Review query filters

3. **Performance Issues**:
   - Monitor database query performance
   - Check embedding generation times
   - Review memory usage patterns

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
streamlit run web_app.py
```

## 📈 Roadmap

### Phase 1: Core Multi-Tenancy ✅
- [x] User authentication with Supabase
- [x] Data isolation with user-specific collections
- [x] Multi-tenant web interface
- [x] Knowledge base CV generation

### Phase 2: Enhanced Features
- [ ] Admin dashboard for user management
- [ ] Usage analytics and reporting
- [ ] Subscription tiers and billing
- [ ] API endpoints for programmatic access

### Phase 3: Advanced Capabilities
- [ ] Team collaboration features
- [ ] CV templates and customization
- [ ] Integration with job boards
- [ ] Mobile application

### Phase 4: Enterprise Features
- [ ] SSO integration
- [ ] Advanced analytics
- [ ] White-label solutions
- [ ] Enterprise security features

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Include docstrings for all classes and methods
- Write tests for new features
- Ensure multi-tenant compatibility

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Supabase** for authentication infrastructure
- **Qdrant** for vector database capabilities
- **OpenAI** for embedding and language model APIs
- **Streamlit** for the web interface framework
- **LangChain** for AI orchestration

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for deployment help
- Review the troubleshooting section above

---

**Built with ❤️ for the future of AI-powered career tools**
