# SECURITY.md - Security & Access Control Requirements

**Last Updated:** 2026-05-08  
**Purpose:** Security implementation details, password policy, session management, and audit trail  
**Note:** For user roles, permissions, and dashboard access, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md)

---

## 1. Password Policy

> **🔗 For user role definitions and feature permissions, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md) (Security & Access Control section).**
>
> This document focuses on security implementation details.

| Requirement | Specification |
|-------------|---------------|
| **Length** | 8-20 characters |
| **Complexity** | Must include: letters, numbers, special characters, uppercase, lowercase |
| **Expiration** | Never expires |
| **History** | Allow reuse of old passwords |
| **Default Admin** | Created on first startup with username: `sanh0605`, password: `sanh0605` |

### **Implementation Requirements:**
- Use bcrypt for password hashing
- Minimum 12 rounds for bcrypt work factor
- Store only password_hash, never plaintext passwords
- Implement secure password reset functionality (if needed)

---

## 2. Session Management

| Requirement | Specification |
|-------------|---------------|
| **Standard Session** | No timeout (stay logged in until logout) |
| **Remember Me Feature** | Must include "Ghi nhớ tôi" checkbox |
| **Remember Me Duration** | 30 days |
| **Password Change** | Session expires immediately |
| **Last Login Display** | Show "Đăng nhập lần cuối: [date/time]" |
| **Logout Confirmation** | Must confirm before actually logging out |

### **Implementation Requirements:**
- Use secure session tokens (cryptographically signed)
- Store sessions with expiration timestamps
- Implement session invalidation on password change
- Use HTTPS-only cookies in production
- Implement CSRF protection for all form submissions
- Secure session storage (encrypted or server-side)

---

## 3. User Roles & Permissions

> **🔗 For complete user role definitions, dashboard access matrix, and feature permissions, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md).**

**Roles Overview:**
- **Admin** (Quản trị viên) - Full system rights
- **Manager** (Quản lý) - Business data management
- **Sales Staff** (Nhân viên bán hàng) - Restricted access

**Implementation Requirements:**
- Role-based access control (RBAC) for all features
- Middleware or decorator pattern for role enforcement
- Secure role storage (not modifiable by users)
- Audit logging for permission denials

---

## 4. Audit Trail

### **A. Track Data Modifications:**

| Action | Track User | Track Date/Time |
|---------|-----------|-----------------|
| **Create records** | ✅ Yes | ✅ Yes |
| **Modify records** | ✅ Yes | ✅ Yes |
| **Delete records** | ✅ Yes | ✅ Yes |

### **B. Track Data Viewing:**

| Activity | Track User | Track Details |
|----------|-----------|--------------|
| **View sensitive data** | ✅ Yes | What was viewed (revenue/profits) |
| **Export reports** | ✅ Yes | Report type, date range, format |
| **Download data files** | ✅ Yes | Filename, table name, date/time |

### **C. Audit Log Configuration:**

| Requirement | Specification |
|-------------|---------------|
| **Log Retention** | 90 days |
| **Access** | Admin only |
| **Tracking Scope** | All modifications, viewing, exports, downloads |

### **Audit Log Fields:**
- Timestamp (Date/Time)
- Username
- Action Type (Create/Modify/Delete/View/Export/Download)
- Record ID/Table
- Details (specific information about the action)

### **Implementation Requirements:**
- Create audit_logs table with proper indexing
- Implement automatic logging for all CRUD operations
- Secure audit log access (Admin only)
- Implement log rotation after 90 days
- Immutable audit entries (cannot be modified/deleted)
- Log export functionality for compliance

---

## 5. Security Implementation Notes

### **Required Security Measures:**
- ✅ All passwords must be hashed using bcrypt
- ✅ Session tokens must be securely generated and stored
- ✅ SQL injection prevention required for all database operations
- ✅ XSS prevention for all user input display
- ✅ CSRF protection required for all form submissions
- ✅ HTTPS required in production environment
- ✅ Regular security updates for all dependencies

### **Database Security:**
- Use parameterized queries (SQLAlchemy ORM handles this)
- Implement foreign key constraints
- Regular database backups
- Secure database file permissions
- Database connection pooling with timeout

### **Application Security:**
- Input validation and sanitization
- Output encoding for user-generated content
- Secure file upload handling
- Rate limiting for API endpoints (if applicable)
- Secure error handling (don't expose sensitive information)

### **Network Security:**
- TLS/SSL encryption for all data in transit
- Secure WebSocket connections (if used)
- Firewall rules for LAN deployment
- Regular security audits and penetration testing

---

## 6. Environment Configuration

### **Required Environment Variables:**
```bash
DATABASE_URL=sqlite:///./dealer_report.db
SECRET_KEY=change-me-in-production-use-strong-random-string
```

### **Implementation Requirements:**
- Never commit `.env` file to version control
- Use strong, randomly generated SECRET_KEY in production
- Implement environment variable validation on startup
- Secure configuration management
- Different configurations for development/staging/production

---

## 7. Compliance & Best Practices

### **Security Best Practices:**
- Follow OWASP Top 10 guidelines
- Implement principle of least privilege
- Regular security training for staff
- Incident response plan
- Security monitoring and alerting

### **Data Protection:**
- Backup encryption (if applicable)
- Secure data retention policies
- Data anonymization for testing (if applicable)
- Compliance with local data protection laws

---

## Summary

This document provides security implementation requirements and best practices. For:

- **User role definitions and permissions** → See [MASTER_DECISIONS.md](MASTER_DECISIONS.md)
- **Dashboard access control** → See [MASTER_DECISIONS.md](MASTER_DECISIONS.md)
- **Feature permission matrix** → See [MASTER_DECISIONS.md](MASTER_DECISIONS.md)
- **Business logic and validation rules** → See [MASTER_DECISIONS.md](MASTER_DECISIONS.md)
- **Database schema and structure** → See [SCHEMA.md](SCHEMA.md)
- **Data validation rules** → See [DATA_VALIDATION.md](DATA_VALIDATION.md)

**Security Implementation Checklist:**
- [ ] Bcrypt password hashing (12+ rounds)
- [ ] Secure session management with expiration
- [ ] CSRF protection for all forms
- [ ] SQL injection prevention (ORM)
- [ ] XSS prevention (output encoding)
- [ ] HTTPS/TLS encryption
- [ ] Audit trail implementation
- [ ] Role-based access control
- [ ] Secure configuration management
- [ ] Regular security updates
