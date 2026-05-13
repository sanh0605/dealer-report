# Dealer Report System

A Streamlit-based reporting platform for wholesale teams to manage data, view performance dashboards, and export reports to PPT/PDF.

## Quick Start

### Prerequisites
- Python 3.11 or higher
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd "DEALER REPORT"
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize database:
```bash
python -m database.seed
```

### Running the Application

Start the Streamlit application:
```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

### Default Login Credentials

| Role      | Username   | Password    |
|-----------|------------|-------------|
| Admin     | sanh0605   | sanh0605    |
| Manager   | manager     | manager123   |
| Sales Staff | employee  | employee123  |

**IMPORTANT:** Change default passwords on first login for production deployment.

## Features

### Data Dashboards (5)
- **Sales & Revenue** (Doanh số & Doanh thu) - Revenue trends, regional breakdown, top dealers
- **Dealer Health** (Sức khỏe Đối tác) - AR aging, payment performance, health scoring
- **Product Performance** (Hiệu suất Sản phẩm) - Inventory status, product analysis, lost sales
- **Field Operations** (Vận động trường) - Visit plans, logs, adherence metrics
- **Profitability** (Hiệu quả Kinh doanh) - Margin analysis, cost structure (Admin/Manager only)

### Utility Pages (3)
- **Upload** - Data import from CSV/Excel files (Admin/Manager only)
- **Lost Sales** - Entry form for missed opportunities (All roles)
- **Admin** - User management and system settings (Admin only)

### Exports
- PDF reports with Vietnamese business format
- PowerPoint presentations for management meetings
- Excel/CSV data downloads

## Technology Stack

- **Frontend:** Streamlit
- **Database:** SQLite with SQLAlchemy ORM
- **Data Processing:** Pandas
- **Charts:** Plotly
- **Exports:** python-pptx (PPT), WeasyPrint (PDF)
- **Testing:** pytest (unit tests), Playwright (E2E)

## Documentation

- `MASTER_DECISIONS.md` - Single source of truth for all business logic
- `SCHEMA.md` - Database structure (13 tables)
- `DASHBOARDS.md` - Dashboard designs
- `DATA_VALIDATION.md` - Validation rules
- `PROJECT_STRUCTURE.md` - File organization
- `DEVELOPMENT.md` - Developer guide

## Security

- Password hashing with bcrypt
- Role-based access control (Admin/Manager/Sales Staff)
- Audit trail for all critical actions
- Session management with 30-day remember option
- CSRF protection enabled

## Language Policy

- **UI:** Vietnamese (all buttons, labels, messages)
- **Code:** English (variables, functions, comments)
- **Documentation:** English

## License

Proprietary - Internal company use only

## Support

For issues or questions, contact the development team.
