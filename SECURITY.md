# Security Guidelines

## Environment Variables

### Sensitive Data
The following environment variables contain sensitive information and **MUST** be kept secure:

- `SECRET_KEY` - Used for JWT token signing
- `DATABASE_URL` - Contains database credentials

### Best Practices

1. **Never commit `.env` files** to version control
   - ✅ `.env.example` is safe (contains no real values)
   - ❌ `.env`, `.env.local`, `.env.compose` should never be committed

2. **Generate Strong SECRET_KEY**
   ```bash
   # Generate a cryptographically secure key
   openssl rand -hex 32
   ```

3. **Rotate Secrets Regularly**
   - Change `SECRET_KEY` periodically
   - Update database passwords on schedule
   - Invalidate old JWT tokens after rotation

4. **Environment-Specific Configuration**
   - Development: `.env.local` or `.env.compose`
   - Production: Use environment variables or secret management service
   - Never use the same `SECRET_KEY` across environments

## Authentication

### JWT Tokens
- Tokens expire after 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Tokens are signed with `SECRET_KEY` using HS256 algorithm
- No token refresh mechanism (re-login required after expiration)

### Password Security
- Passwords are hashed using bcrypt with automatic salt
- Minimum password requirements should be enforced at application level
- Original passwords are never stored or logged

## Production Deployment

### Required Changes

1. **Generate new SECRET_KEY**
   ```bash
   openssl rand -hex 32
   ```

2. **Use Strong Database Credentials**
   - Change default `time-user:time-pw`
   - Use complex, randomly generated passwords

3. **Enable HTTPS**
   - Use TLS/SSL certificates
   - Redirect HTTP to HTTPS
   - Set secure cookie flags

4. **Configure CORS Properly**
   ```python
   # Add to main.py
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # Specific origins only
       allow_credentials=True,
       allow_methods=["GET", "POST"],
       allow_headers=["*"],
   )
   ```

5. **Rate Limiting**
   - Implement rate limiting for authentication endpoints
   - Protect against brute force attacks

6. **Logging and Monitoring**
   - Log authentication failures
   - Monitor for suspicious activity
   - Never log passwords or tokens

## Database Security

1. **Use Connection Pooling**
   - Configure max connections in production
   - Use read replicas for analytics queries

2. **Enable SSL for Database Connections**
   ```env
   DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db?sslmode=require
   ```

3. **Backup Encryption**
   - Encrypt database backups
   - Store backups in separate, secure location

## API Security

### Endpoints Protection
- Authentication required endpoints use `Depends(get_current_active_user)`
- Superuser-only endpoints use `Depends(get_current_superuser)`

### Input Validation
- All inputs validated with Pydantic models
- SQL injection prevented by using SQLModel ORM
- No raw SQL queries without parameterization

## Vulnerability Reporting

If you discover a security vulnerability, please email: security@yourdomain.com

**Do not open public issues for security vulnerabilities.**

## Dependencies

Keep dependencies updated:
```bash
pip list --outdated
pip install --upgrade package-name
```

Review security advisories:
- [GitHub Security Advisories](https://github.com/advisories)
- [PyPI Security Advisories](https://pypi.org/security/)

## Compliance

- GDPR: Implement data deletion endpoints
- Privacy: Add privacy policy and data collection disclosure
- Audit: Log all data access and modifications
