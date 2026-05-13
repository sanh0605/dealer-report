# DOCUMENTATION INDEX - All Project Documentation

**Last Updated:** 2026-05-08  
**Purpose:** Quick index to all project documentation and their purposes

---

## 📁 Core Documentation Files

### **MASTER_DECISIONS.md** ⭐ **START HERE - SINGLE SOURCE OF TRUTH**
- **Purpose:** Single source of truth for all implementation decisions
- **Content:** Complete summary of all business logic, security requirements, dashboard designs, validation rules, language policy, export formats
- **Usage:** Read this first for understanding all system requirements and rules
- **Critical Status:** MUST follow all rules documented here during implementation
- **Contains:** Business rules, user roles, language policy, date formats, export formats, validation workflows

### **SCHEMA.md**
- **Purpose:** Database schema and structure reference
- **Content:** All 11 database tables with field descriptions, auto-assignment logic (brand_group, region)
- **Usage:** Reference for understanding data structure and relationships
- **Note:** For business logic and system configuration, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md)
- **Last Updated:** 2026-05-08

### **SECURITY.md**
- **Purpose:** Security implementation details and requirements
- **Content:** Password policy, session management, audit trail requirements, security implementation notes
- **Usage:** Reference for implementing authentication, authorization, and security features
- **Note:** For user roles and permissions, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md)
- **Last Updated:** 2026-05-08

### **DASHBOARDS.md**
- **Purpose:** Complete dashboard design specifications
- **Content:** 5 dashboard designs with Vietnamese UI, KPIs, charts, tables, filters
- **Usage:** Reference for implementing Streamlit dashboard pages
- **Key Features:** Sales, Dealer Health, Product Performance, Field Operations, Profitability dashboards

### **DATA_VALIDATION.md**
- **Purpose:** Table-specific validation rules for all 11 database tables
- **Content:** Validation rules for all tables, error messages in Vietnamese
- **Usage:** Reference for implementing data upload service and validation logic
- **Note:** For date format recognition and validation workflows, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md)
- **Last Updated:** 2026-05-08

### **PROJECT_STRUCTURE.md** 🏗️
- **Purpose:** Complete project directory & file organization reference
- **Content:** Current project structure vs. planned structure, file-by-file breakdown, implementation order
- **Usage:** Reference for understanding project organization and what needs to be created
- **Contains:** Directory trees, file purposes, creation order, statistics
- **Last Updated:** 2026-05-08

### **YEAR_TARGET_REPORT.md** 📊
- **Purpose:** Year Target Observation Report specification (PPT/PDF export)
- **Content:** Complete report structure with 9 sections in Vietnamese, data sources, calculations, export formats
- **Usage:** Reference for implementing annual target tracking and reporting feature
- **Key Features:** Executive summary, regional performance, brand analysis, dealer ranking, inventory status, field operations, AR tracking, profitability analysis
- **Access Level:** Admin & Manager only (Sales Staff restricted)
- **Last Updated:** 2026-05-08

---

## 📋 Implementation Plan

### **docs/superpowers/plans/2026-04-28-dealer-report-full-build.md** ⭐ **IMPLEMENTATION GUIDE**
- **Purpose:** Comprehensive step-by-step implementation guide
- **Content:** 8-phase development plan with specific tasks, file map, tech stack, pre-coding fixes
- **Usage:** Follow this plan for systematic development - includes TDD approach, testing strategy, and deployment
- **Status:** Updated with all pre-coding fixes and business logic decisions
- **Contains:** 20 specific tasks with code examples, file structures, and verification steps

---

## 🎯 Quick Reference Guides

### **When You Need to Know:**

#### **Database Structure?**
→ **Read:** `SCHEMA.md`
- All 11 tables with field descriptions
- Auto-assignment logic for brand_group and region
- **Note:** Business rules are in [MASTER_DECISIONS.md](MASTER_DECISIONS.md)

#### **Security Implementation?**
→ **Read:** `SECURITY.md`
- Password policy (8-20 chars, complexity required)
- Session management (no timeout, 30-day remember me)
- Audit trail (90-day retention, Admin only access)
- **Note:** User roles and permissions are in [MASTER_DECISIONS.md](MASTER_DECISIONS.md)

#### **Dashboard Design?**
→ **Read:** `DASHBOARDS.md`
- 5 complete dashboard specifications
- Vietnamese UI labels and chart types
- KPIs, filters, and interactive features
- All charts and tables specifications

#### **Year Target Report?**
→ **Read:** `YEAR_TARGET_REPORT.md`
- 9-section annual target observation report (PPT/PDF export)
- Vietnamese UI labels and comprehensive business metrics
- Executive summary, regional/brand/dealer performance, inventory, field operations, AR, profitability
- Report generation workflow and export formats
- **Access Level:** Admin & Manager only

#### **Data Validation Rules?**
→ **Read:** `DATA_VALIDATION.md`
- Validation rules for all 11 tables
- Error messages in Vietnamese
- **Note:** Date format recognition is in [MASTER_DECISIONS.md](MASTER_DECISIONS.md)

#### **Business Logic?**
→ **Read:** `MASTER_DECISIONS.md` ⭐
- Lost sales calculation rules (cascading formula)
- Visit adherence definition (structured outcomes + free notes)
- AR aging configuration (bucket_size + max_days)
- All other business rules and decisions
- Language policy and date formats
- Export formats (PPT/PDF)
- User roles and permissions

#### **Implementation Requirements?**
→ **Read:** `MASTER_DECISIONS.md`
- All requirements in one document
- Must-follow rules for implementation
- Technology stack and approach
- Next steps and priorities

---

## 🔄 Documentation Structure & Relationships

### **Single Source of Truth:**
```
MASTER_DECISIONS.md (Top Level - All Business Logic, Rules, Policies)
├── Referenced by SCHEMA.md (for business rules, language policy)
├── Referenced by SECURITY.md (for user roles, permissions)
├── Referenced by DATA_VALIDATION.md (for date formats, validation workflows)
└── Referenced by all implementation documents
```

### **Focused Documentation:**
```
SCHEMA.md - Database structure & auto-assignment logic only
SECURITY.md - Security implementation details only
DATA_VALIDATION.md - Table-specific validation rules only
DASHBOARDS.md - Dashboard design specifications only
```

### **Implementation Plan:**
```
docs/superpowers/plans/2026-04-28-dealer-report-full-build.md (Comprehensive implementation guide)
```

---

## 📝 Maintenance Workflow

### **When Updating Documentation:**

1. **Update MASTER_DECISIONS.md First**
   - This is the single source of truth
   - All business rules, policies, and decisions go here
   - Update timestamp at the top

2. **Update Specific Documents**
   - SCHEMA.md for database structure changes
   - SECURITY.md for security implementation changes
   - DATA_VALIDATION.md for validation rule changes
   - DASHBOARDS.md for dashboard design changes

3. **Update References**
   - Ensure cross-references between documents are accurate
   - Add/update notes pointing to MASTER_DECISIONS.md when appropriate

4. **Update DOCUMENTATION_INDEX.md**
   - Update this index if structure changes
   - Update "Last Updated" timestamps
   - Maintain consistency with actual file structure

5. **Test the Documentation**
   - Try to find specific information using this index
   - Verify all links and references work
   - Ensure no contradictions between documents

---

### **What Goes Where:**

| Content Type | Primary Location | Referenced By |
|-------------|------------------|---------------|
| **Business Rules** | MASTER_DECISIONS.md | SCHEMA.md, DATA_VALIDATION.md |
| **User Roles & Permissions** | MASTER_DECISIONS.md | SECURITY.md |
| **Language Policy** | MASTER_DECISIONS.md | SCHEMA.md, DATA_VALIDATION.md |
| **Date Formats** | MASTER_DECISIONS.md | DATA_VALIDATION.md |
| **Export Formats** | MASTER_DECISIONS.md | All export-related code |
| **Database Structure** | SCHEMA.md | Implementation code |
| **Security Implementation** | SECURITY.md | Auth service, session management |
| **Validation Rules** | DATA_VALIDATION.md | Upload service |
| **Dashboard Design** | DASHBOARDS.md | Dashboard pages |
| **Year Target Report** | YEAR_TARGET_REPORT.md | Report generation service |

---

## ⚡ Quick Access Summary

| Question | Read This File |
|-----------|----------------|
| What rules must I follow? | `MASTER_DECISIONS.md` ⭐ |
| What's the database structure? | `SCHEMA.md` |
| What security features needed? | `SECURITY.md` |
| What should dashboards look like? | `DASHBOARDS.md` |
| How to validate data? | `DATA_VALIDATION.md` |
| What's the project structure? | `PROJECT_STRUCTURE.md` |
| What's the Year Target Report? | `YEAR_TARGET_REPORT.md` |
| What's the implementation plan? | `docs/superpowers/plans/2026-04-28-dealer-report-full-build.md` |

---

## 🎯 Critical Rules

### **Must Follow Strictly During Implementation:**

1. **Start with MASTER_DECISIONS.md** - Contains all critical rules (single source of truth)
2. **All UI in Vietnamese** - No English visible to end users
3. **TDD Approach** - Write failing tests first, then implement
4. **Role-Based Access** - Respect Admin/Manager/Sales Staff permissions
5. **Audit Trail** - Log all critical actions (Admin only access)
6. **Validation First** - No data enters without passing validation
7. **Error Messages** - All in Vietnamese
8. **Configuration** - Use .env file, never hardcode credentials

### **Documentation Principles:**

- **Single source of truth:** MASTER_DECISIONS.md for all business logic, rules, and policies
- **Focused documents:** Each .md file has a clear, specific purpose
- **Cross-reference:** Use references to avoid duplication
- **Keep rules in one place:** Business logic belongs in MASTER_DECISIONS.md
- **Update documentation BEFORE implementation changes**
- **Maintain consistency:** Ensure all references are accurate

---

## 📞 Documentation Version Control

### **Current Documentation Version:** 3.1 (2026-05-11)

**Changes in Version 3.1:**
- ✅ **REMAINING INCONSISTENCIES RESOLVED** - Fixed 5 additional inconsistencies
- ✅ **Chart Types:** Added "horizontal bar" to MASTER_DECISIONS.md chart types list
- ✅ **Lost Sales Validation:** Explicitly documented that lost_volume must be positive in MASTER_DECISIONS.md
- ✅ **Sub-Region Validation:** Added reference to MASTER_DECISIONS.md in SCHEMA.md for sales_targets validation workflow
- ✅ **Visit Result Format:** Standardized visit result format between MASTER_DECISIONS.md and DASHBOARDS.md
- ✅ **REDAUNDANCIES REDUCED** - Replaced duplicate content with references to MASTER_DECISIONS.md
- ✅ **Negative Values:** Replaced SCHEMA.md "Negative Value Handling" section with reference to MASTER_DECISIONS.md
- ✅ **Order ID:** Replaced SCHEMA.md "Order ID Handling" section with reference to MASTER_DECISIONS.md
- ✅ **Region Assignment:** Replaced duplicate region auto-assignment logic with reference to MASTER_DECISIONS.md
- ✅ **AMBIGUITIES RESOLVED** - Documented 9 explicit implementation decisions in MASTER_DECISIONS.md
- ✅ **Foreign Key Constraint:** Documented plan_id as application-level only (no DB constraint)
- ✅ **Session Storage:** Documented Streamlit session state for LAN deployment
- ✅ **Lost Sales Calculation:** Documented real-time calculation at time of entry
- ✅ **Chart Export:** Documented conversion to static PNG images for PDF
- ✅ **Audit Log Retention:** Documented automated cleanup on app startup
- ✅ **Concurrent Access:** Documented SQLite approach for ~10 users
- ✅ **TDD Scope:** Documented TDD for services only, manual UI testing
- ✅ **Character Encoding:** Documented UTF-8 for Vietnamese characters
- ✅ **Error Handling:** Documented Karpathy Guidelines approach
- ✅ **MASTER_DECISIONS.md:** Updated to version 3.2 with "Ambiguity Resolutions" section

**Changes in Version 3.0:**
- ✅ **CRITICAL DOCUMENTATION RESOLUTIONS** - Fixed 5 critical inconsistencies identified in workspace audit
- ✅ **Table Count:** Confirmed 13 tables (11 business + 2 system) - updated implementation plan test to include audit_logs
- ✅ **Dashboard Structure:** Renamed 5_Inventory.py to 5_Profitability_Dashboard.py, inventory integrated into Product Performance Dashboard
- ✅ **Role Naming:** Standardized to "Sales Staff" (replaced "Employee") across all documentation
- ✅ **Location Region:** Marked inventory_status.location_region as required (was inconsistent)
- ✅ **Page Numbering:** Assigned proper page number (5) to Profitability Dashboard
- ✅ **MASTER_DECISIONS.md:** Updated to version 3.1 with "Critical Documentation Resolutions" section documenting all fixes
- ✅ **Implementation Plan:** Updated all references to match corrected structure

**Changes in Version 2.5:**
- ✅ Added YEAR_TARGET_REPORT.md - comprehensive Year Target Observation Report specification
- ✅ DOCUMENTATION_INDEX.md updated to include YEAR_TARGET_REPORT.md in all reference sections
- ✅ Added Year Target Report to "Quick Reference Guides" and "Quick Access Summary"
- ✅ Updated "What Goes Where" table to include Year Target Report content type
- ✅ Complete annual target tracking and reporting specification now documented

**Changes in Version 2.4:**
- ✅ Removed Vietnamese language policy duplication from CLAUDE.md and DASHBOARDS.md
- ✅ Established MASTER_DECISIONS.md as single source of truth for language policy
- ✅ Added references to MASTER_DECISIONS.md in CLAUDE.md and DASHBOARDS.md
- ✅ Maintained contextual Vietnamese mentions where appropriate for document clarity

**Changes in Version 2.3:**
- ✅ Added PROJECT_STRUCTURE.md - comprehensive project directory & file organization reference
- ✅ DOCUMENTATION_INDEX.md updated to include PROJECT_STRUCTURE.md
- ✅ Complete project structure documentation now exists (not just in memory)

**Changes in Version 2.2:**
- ✅ Removed PLAN.md (redundant with detailed implementation plan)
- ✅ Updated DOCUMENTATION_INDEX.md to reference single implementation guide
- ✅ Removed .claude/settings.local.json (local development config)
- ✅ Streamlined documentation structure for clarity

**Changes in Version 2.1:**
- ✅ Cleaned up unnecessary documentation files
- ✅ Removed MVP.md (superseded by full production system)
- ✅ Removed AUDIT_REPORT.md (historical audit document)
- ✅ Removed CONTENT_DUPLICATION_FIX.md (temporary fix summary)
- ✅ Removed .superpowers/brainstorm/ (old brainstorming content)
- ✅ Updated DOCUMENTATION_INDEX.md to reflect clean structure

**Changes in Version 2.0:**
- ✅ Eliminated content duplication across documents
- ✅ Established MASTER_DECISIONS.md as single source of truth
- ✅ Cleaned SCHEMA.md to focus on database structure only
- ✅ Cleaned SECURITY.md to focus on security implementation only
- ✅ Cleaned DATA_VALIDATION.md to focus on table-specific validation only
- ✅ Added cross-references between documents
- ✅ Updated maintenance workflow guidelines

**Version 1.0 (Initial):**
- Complete documentation set created
- All business rules and specifications documented
- Planning phase completed

---

**This index helps you quickly find the right documentation for any question or implementation task. For the most accurate and up-to-date information, always start with MASTER_DECISIONS.md.**
