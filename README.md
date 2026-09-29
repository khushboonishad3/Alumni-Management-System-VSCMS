# CMS Kanpur BCA & MCA Alumni Technical Networking & Mentorship Platform

> Production-ready Alumni Management, Developer Networking, Mentorship, Internal Placement Referrals, and Capstone Collaboration Ecosystem for **Dr. Virendra Swarup College of Management Studies (CMS Kanpur)**.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel%20Production-blue?style=for-the-badge&logo=vercel)](https://alumnimanagementsystemvscms.vercel.app/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/Database-Neon%20Postgres-336791?style=for-the-badge&logo=postgresql)](https://neon.tech)
[![Python 3.14](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python)](https://python.org)

🚀 **Live Working Platform**: [https://alumnimanagementsystemvscms.vercel.app/](https://alumnimanagementsystemvscms.vercel.app/)

---

## ⚡ Quick Start: Demo Login Accounts

Test the live deployment immediately using these pre-seeded institutional accounts:

| Role | Email | Password | Access Scope & Highlights |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `superadmin@cmskanpur.edu.in` | `Admin@CMS2025` | Full system control, role elevation, create projects & resources, audit logs |
| **Admin** | `admin@cmskanpur.edu.in` | `Admin@CMS2025` | User management, post industry projects, share technical resources, jobs |
| **Faculty** | `faculty.cs@cmskanpur.edu.in` | `Faculty@CMS2025` | Student verification queue, post capstones, share technical resources, analytics |
| **Alumni (Microsoft)**| `aarav.sharma@microsoft.com` | `Alumni@CMS2025` | Post jobs & referrals, post industry projects, share resources, mentorship |
| **Alumni (Amazon)** | `priya.verma@amazon.com` | `Alumni@CMS2025` | Referral requests, mock interviews, 1-on-1 mentorship, publish resources |
| **Student (BCA)** | `aditya.tiwari@cmskanpur.edu.in` | `Student@CMS2025` | Request referrals, submit project proposals, book mentorship, download resources |
| **Student (MCA)** | `ritu.yadav@cmskanpur.edu.in` | `Student@CMS2025` | Universal search, event RSVPs, project proposals |

---

## 🛠️ Recent Deployments & Architectural Upgrades

The platform includes the following latest architectural and user experience improvements:

1. **Live Vercel Production Deployment**:
   - Live URL: [https://alumnimanagementsystemvscms.vercel.app/](https://alumnimanagementsystemvscms.vercel.app/)
   - Integrated custom `VercelASGIPathMiddleware` and route rewrites to support clean Single-Page Application (SPA) path handling and backend REST API routing under serverless execution.
2. **Neon Serverless PostgreSQL Integration**:
   - Production database powered by cloud serverless PostgreSQL (`Neon.tech`) with resilient multi-driver fallback (`pg8000` / `psycopg2-binary`).
   - Dynamic zero-downtime startup schema synchronization ensuring columns and indices match declarative models.
3. **Tailored Role-Specific Profiles**:
   - **Super Admin, Admin, and Faculty**: Student-specific fields (`course`, `current_semester`, `cgpa`, and `about/bio`) have been removed from both backend API payloads and frontend profile dashboards.
   - Replaced with dedicated professional fields: **Full Name**, **Educational Qualification** (e.g., M.Tech, Ph.D., MCA), **Technical Skills**, and **Professional & Development Profiles** (dynamic links for GitHub, LinkedIn, Google Scholar, ResearchGate, personal sites).
   - Students and Alumni retain specialized academic and industry career profiles.
4. **Decentralized Project & Resource Creation**:
   - **Industry Projects (Capstone Problem Statements)**: Super Admin, Admin, Faculty, and Alumni can now all post real-world problem statements with tech stacks, difficulty levels, duration, and maximum team sizes.
   - **Technical Resource Library**: Super Admin, Admin, Faculty, and Alumni can now all upload and publish curated technical study materials, DSA cheat sheets, architecture blueprints, and repositories.
5. **Streamlined Pure Email/Password Authentication**:
   - Removed captcha friction while preserving strong password hashing (PBKDF2-HMAC-SHA256), JWT token issuance, RBAC checks, and audit logging.

---

## 1. Project Overview

The **CMS AlumniConnect** platform is specifically designed for the students, faculty, and alumni of the Department of Computer Applications (BCA & MCA) at **Dr. Virendra Swarup College of Management Studies (CMS Kanpur)**. 

Unlike traditional static alumni directories, this system functions as a **complete technical collaboration ecosystem**:
- **Developer-Centric Alumni Directory**: Search and filter alumni by verified college batch (2018–2024), BCA/MCA program, programming languages, cloud stacks, and company affiliation (Microsoft, Amazon, Zomato, Paytm, TCS, Infosys). Cards feature interactive 1-click **Referral Ready** and **Mentor** request triggers.
- **Internal Placement Referrals & Job Details Inspector**: Direct referral pipeline and comprehensive interactive job viewer with detailed candidate requirements, technical skills chips, experience levels, and direct internal referral dispatch.
- **1-on-1 Mentorship & Mock Interviews**: Direct booking of Technical, Coding DSA, System Design, and HR mock interviews.
- **Resume Reviews**: Alumni provide line-by-line feedback, scoring, and suggestions for ATS-ready resumes.
- **Industry Capstone Projects**: Alumni post real-world production problem statements; students submit team proposals under faculty co-guidance.
- **Institutional Verification Engine**: Automated validation against pre-authorized CMS Kanpur institutional enrollment rosters with an administrative review queue.
- **Technical Resource Library**: Curated repository for DSA roadmaps, production FastAPI architectures, SQL cheat sheets, and placement archives.
- **Events & Hackathons**: In-app hosting and RSVP registration for hackathons, tech fests, masterclasses, webinars, and guest lectures.
- **Administrative Control & Analytics**: Visual charts for graduation cohorts, top hiring employers, in-demand technical skills, and audit trails.

---

## 2. Key Features

1. **Role-Based Access Control (RBAC)**: Fine-grained permissions across 5 roles: `Student`, `Alumni`, `Faculty`, `Admin`, and `Super Admin`.
2. **Institutional Roster Auto-Verification**: During registration, roll numbers and enrollment numbers are automatically verified against the college dataset (`AuthorizedCollegeRegistry`).
3. **Interactive Directory Badges**: Direct click-to-request triggers on alumni cards—clicking `Referral Ready` launches a pre-filled referral request modal; clicking `Mentor` opens 1-on-1 mentorship booking.
4. **Comprehensive Job Details & Referral Viewer**: Clickable job cards and deep-linked `#jobs/<id>` routing opening a rich modal with required tech stack tags, experience eligibility, full job descriptions, and fast-track alumni referral triggers.
5. **Decentralized Event & Hackathon Hosting**: Verified Alumni, Faculty, and Admins can publish upcoming webinars, coding competitions, and hackathons with customizable attendee capacities and RSVP role selection (Hacker, Mentor, Judge, Speaker).
6. **Internal Messaging & Notification Center**: Real-time 1-on-1 messaging and in-app notifications without exposing personal phone numbers or private emails.
7. **Multi-Entity Universal Search**: Instant global search across Alumni, Jobs, Projects, Resources, and Events simultaneously.
8. **Multi-Stack Backend Compatibility**: Fully documented architectural mappings for **Java Spring Boot**, **PHP Laravel**, and **C# ASP.NET Core** that preserve the exact database schema and REST API contracts.

---

## 3. System Architecture

```
                      +-------------------------------------------------------+
                      |               CMS Kanpur Client Layer                 |
                      |   Desktop / Laptop / Tablet / Mobile (Responsive UI)  |
                      |   (HTML5, CSS3 Glassmorphic System, Vanilla JS SPA)   |
                      +---------------------------+---------------------------+
                                                  | REST API / JSON
                                                  v
                      +-------------------------------------------------------+
                      |                   FastAPI Gateway                     |
                      |    JWT Auth / CORS / RBAC Dependency Filters / Audit  |
                      +----+----------------------+-----------------------+---+
                           |                      |                       |
            +--------------v---+           +------v-----------+    +------v----------+
            | Users & Profiles |           | Placement Hub    |    | Mentorship      |
            | - StudentProfile |           | - Jobs           |    | - MentorProfile |
            | - AlumniProfile  |           | - Applications   |    | - MockInterview |
            | - Registry Match |           | - Referrals      |    | - ResumeReview  |
            +------------------+           +------------------+    +-----------------+
                           |                      |                       |
            +--------------v---+           +------v-----------+    +------v----------+
            | Industry Projects|           | Tech Resources   |    | Events & Meet   |
            | - Problem Stmts  |           | - Categorized Lib|    | - Hackathons    |
            | - Proposals      |           | - Versioned Docs |    | - Webinars      |
            +------------------+           +------------------+    +-----------------+
                                                  |
                           +----------------------+----------------------+
                           |                                             |
                           v                                             v
            +------------------------------+              +------------------------------+
            |   Relational Database Layer  |              | Secure Media Storage Layer   |
            |   PostgreSQL / SQLite Engine |              | Local / S3-compatible Blobs  |
            |   SQLAlchemy 2.0 ORM         |              | (Resumes, Avatars, Materials)|
            +------------------------------+              +------------------------------+
```

---

## 4. Technology Stack

- **Backend**: Python 3.14+ with FastAPI, Pydantic v2, and SQLAlchemy 2.0.
- **Frontend**: HTML5, CSS3 with custom design tokens, modern Bootstrap 5.3, Bootstrap Icons, Chart.js for data visualization, and Vanilla JS SPA routing.
- **Database**: PostgreSQL 16 (production) / SQLite (zero-setup development).
- **Authentication**: PBKDF2-HMAC-SHA256 password hashing and signed JWT tokens (`HS256`).
- **Testing**: Pytest with automated end-to-end API test suites.
- **Containerization**: Docker and Docker Compose.

---

## 5. Installation

### Prerequisites
- Python 3.10+ (Python 3.14 recommended)
- Git

### Clone & Setup
```bash
# 1. Clone the repository
git clone https://github.com/ashutosh-cms/cms-kanpur-alumni-platform.git
cd "kb aumni vscms"

# 2. Install dependencies
pip install -r requirements.txt
```

---

## 6. Environment Variables

Create a `.env` file based on `.env.example`:

```ini
ENV=development
DEBUG=True
DATABASE_URL=sqlite:///./cms_alumni.db
SECRET_KEY=cms-kanpur-bca-mca-super-secret-jwt-key-2025-secure-hash
ACCESS_TOKEN_EXPIRE_MINUTES=1440
COLLEGE_NAME="Dr. Virendra Swarup College of Management Studies (CMS Kanpur)"
```

For PostgreSQL:
```ini
DATABASE_URL=postgresql://cms_user:cms_password_2025@localhost:5432/cms_alumni_db
```

---

## 7. Database Setup & Seed Data

The application includes an automated seeder populated with realistic CMS Kanpur BCA and MCA data:

```bash
# Run database setup and rich seed data
python -m app.seed_data
```

This creates:
- Pre-authorized CMS Kanpur institutional enrollment rosters.
- Default Super Admin, Admin, and Faculty accounts.
- Verified alumni at Microsoft, Amazon, Zomato, Paytm, TCS, and Infosys.
- Active BCA & MCA students with GitHub, LinkedIn, and LeetCode profiles.
- Live jobs, referral requests, mentorship sessions, mock interviews, and capstone problems.

---

## 8. Migration Instructions

The platform uses SQLAlchemy declarative tables. When upgrading schemas:
```bash
# Verify database connection and schema initialization
python -c "from app.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine); print('Database tables verified!')"
```

---

## 9. Running Locally

Start the development server:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Then visit:
- **Interactive Web App**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Seed Demo Credentials
| Role | Email | Password |
| :--- | :--- | :--- |
| **Super Admin** | `superadmin@cmskanpur.edu.in` | `Admin@CMS2025` |
| **Admin** | `admin@cmskanpur.edu.in` | `Admin@CMS2025` |
| **Faculty** | `faculty.cs@cmskanpur.edu.in` | `Faculty@CMS2025` |
| **Alumni (Microsoft)**| `aarav.sharma@microsoft.com` | `Alumni@CMS2025` |
| **Alumni (Amazon)** | `priya.verma@amazon.com` | `Alumni@CMS2025` |
| **Student (BCA)** | `aditya.tiwari@cmskanpur.edu.in` | `Student@CMS2025` |
| **Student (MCA)** | `ritu.yadav@cmskanpur.edu.in` | `Student@CMS2025` |

---

## 10. API Documentation

Detailed endpoint schemas and payload specifications are available in [docs/API_DOCUMENTATION.md](file:///c:/Users/Ashutosh/OneDrive/Desktop/kb%20aumni%20vscms/docs/API_DOCUMENTATION.md).

Key Endpoint Groups:
- `/api/auth`: Registration, Login, Current User (`/me`), Password Reset.
- `/api/alumni`: Advanced multi-filter search, profile details, showcase projects.
- `/api/jobs`: Job postings, internship filters, job applications, referral requests.
- `/api/mentorship`: Mentor directory, session scheduling, mock interviews, resume reviews.
- `/api/projects`: Industry problem statements, proposal submissions, milestone tracking.
- `/api/resources`: Categorized library, download tracking, file uploads.
- `/api/events`: Flagship hackathons, tech fests, webinars, registrations.
- `/api/admin`: Analytics metrics, verification approval queue, user administration, audit logs.
- `/api/search`: Multi-entity universal global search.

---

## 11. User Roles & Permissions

| Role | Core Purpose & Scope | Key Capabilities & Post Permissions |
| :--- | :--- | :--- |
| **Student** | Active BCA & MCA students seeking career acceleration | • Explores verified alumni directory<br>• Views complete job descriptions & candidate requirements<br>• Applies to jobs & requests internal employee referrals<br>• Books 1-on-1 mentorship & coding mock interviews<br>• Submits industry capstone project proposals<br>• Registers/RSVPs for hackathons & tech events<br>• **Maintains Student Profile & Resume**<br>• ⚠️ *Posting placement opportunities and hosting events/hackathons is restricted from student accounts* |
| **Alumni** | Verified graduates working across global tech firms | • **Maintains Developer & Professional Profile** (experience, GitHub, LeetCode)<br>• **Posts Job & Internship Openings** (`+ Post Opportunity`) with employee referral support<br>• **Hosts Webinars, Masterclasses & Hackathons** (`+ Host Event / Hackathon`)<br>• **Posts Industry Problem Statements** (`+ Post Problem Statement`)<br>• **Shares Technical Resources** (`+ Share Technical Resource`)<br>• Provides 1-on-1 mentorship, DSA coaching & resume reviews |
| **Faculty** | BCA/MCA professors, HODs & academic coordinators | • Reviews & approves pending student and alumni verifications<br>• Views institutional placement analytics & cohort distribution charts<br>• **Posts Industry Problem Statements & Capstone Projects**<br>• **Publishes Technical Resources & Study Guides**<br>• **Posts Academic Internships & Research Fellowships**<br>• Organizes departmental workshops, tech fests & guest lectures<br>• *(Profile sections & alerts removed; exclusive to Student & Alumni)* |
| **Admin** | College IT administrators & Placement (T&P) officers | • Day-to-day community moderation & operational governance<br>• **User Account Administration**: Activates or suspends user accounts<br>• **Posts Industry Problem Statements & Technical Resources**<br>• Broadcasts college newsletters with automated in-app alerts<br>• Inspects security & operational audit logs<br>• Posts campus placement drives & corporate tie-ups<br>• *(Profile sections & alerts removed; exclusive to Student & Alumni)* |
| **Super Admin** | Director, Principal or Lead System Architect | • **Root System Authority** & institutional configuration<br>• **Exclusive User Role Elevation** (`PUT /api/admin/users/{id}/role`): Promotes/demotes users between Student, Alumni, Faculty, and Admin<br>• **Posts Industry Projects & Technical Resources**<br>• Protected immunity against deactivation<br>• Complete database, audit trail, and operational override powers<br>• *(Profile sections & alerts removed; exclusive to Student & Alumni)* |

---

## 12. Security Architecture

1. **Password Hashing**: PBKDF2 with SHA-256 (100,000 rounds) using a cryptographically secure random salt (`os.urandom(16)`).
2. **Contact Details Privacy**: Private email addresses and phone numbers are hidden from public API responses unless explicitly opted in or viewed by administrators.
3. **Backend Authorization**: Role checks (`require_roles`) and verification checks (`require_verified_user`) are enforced on every route.
4. **File Upload Restrictions**: File extensions are strictly validated against whitelists (Images: `.jpg`, `.png`, `.webp`; Resumes: `.pdf`, `.docx`).
5. **SQL Injection Defense**: All queries are parameterized via SQLAlchemy ORM.
6. **Audit Trails**: Sensitive administrative actions and logins are logged in the `audit_logs` table.

---

## 13. Deployment

### Docker Deployment
```bash
# Start application and PostgreSQL with Docker Compose
docker-compose up -d --build

# Inspect running containers
docker-compose ps
```

The application runs on `http://localhost:8000` with PostgreSQL 16 on `localhost:5432`.

---

## 14. Backup Strategy

1. **Database Snapshots**:
   ```bash
   # PostgreSQL daily automated backup
   pg_dump -U cms_user -h localhost -d cms_alumni_db -F c -b -v -f "/backups/cms_alumni_$(date +%Y%m%d).dump"
   ```
2. **Media Storage**: Daily rsync or S3 bucket replication for the `media/` folder.
3. **Disaster Recovery**: Automated retention policy keeping 7 daily, 4 weekly, and 12 monthly snapshots.

---

## 15. Cross-Platform Architectural Compatibility

The platform provides complete architectural migration guides showing how the backend can be mapped to other languages without altering the database schema or frontend:
- [Java Spring Boot Architecture Guide](file:///c:/Users/Ashutosh/OneDrive/Desktop/kb%20aumni%20vscms/docs/JAVA_SPRING_BOOT_ARCHITECTURE.md)
- [PHP Laravel Architecture Guide](file:///c:/Users/Ashutosh/OneDrive/Desktop/kb%20aumni%20vscms/docs/PHP_LARAVEL_ARCHITECTURE.md)
- [C# ASP.NET Core Architecture Guide](file:///c:/Users/Ashutosh/OneDrive/Desktop/kb%20aumni%20vscms/docs/DOTNET_ASPNET_CORE_ARCHITECTURE.md)

---

## 16. Automated Test Suite

Run the full pytest suite:
```bash
python -m pytest tests/test_api.py -v
```

All 20 automated test cases validate authentication, student posting restrictions for placements/events, role-specific profile access exclusivity, project and resource creation across faculty/alumni/admin roles, institutional auto-verification, alumni multi-filter search, referral workflows, mentorship, and security boundaries.

---

&copy; 2026 Dr. Virendra Swarup College of Management Studies (CMS Kanpur). Built for the BCA & MCA Technical Community.
