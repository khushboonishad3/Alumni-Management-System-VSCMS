# CMS Kanpur BCA & MCA Alumni Technical Platform - System Architecture

## 1. Executive Overview

The **CMS Kanpur BCA & MCA Alumni Technical Networking, Mentorship, and Placement Platform** is engineered specifically for the Department of Computer Applications at **Dr. Virendra Swarup College of Management Studies (CMS Kanpur)**.

Unlike generic corporate alumni portals or static directories, this system functions as an integrated **technical collaboration ecosystem** combining:
- **Developer-Centric Alumni Directory**: Deep-indexing by skills (Python, Java, Spring Boot, React, AWS, Docker), graduation batch, and company affiliation.
- **Career & Internal Referral Engine**: Direct alumni referral requests with complete privacy protection (no raw contact leaks).
- **1-on-1 Mentorship & Mock Interviews**: Dedicated workflows for technical interviews, system design discussions, and resume reviews.
- **Industry Projects & Problem Statements**: Alumni-sponsored real-world problem statements for student capstone projects with faculty co-guidance.
- **Institutional Verification Engine**: Automated pre-authorized validation against CMS Kanpur enrollment and roll numbers with an administrative approval queue.

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

## 2. Multi-Tier Architecture

### 2.1 Presentation Layer (Frontend)
- Modern Responsive Web UI built with semantic HTML5, custom CSS3 design tokens, and lightweight Bootstrap 5.
- Client-Side Hash Routing (`#home`, `#alumni`, `#jobs`, `#mentorship`, `#projects`, `#resources`, `#events`, `#messages`, `#profile`, `#admin`).
- Real-time debounced universal global search across all system entities.
- Dynamic data visualization via Chart.js for batch distributions, company clusters, and skill demand.

### 2.2 Application & Business Logic Layer (FastAPI Backend)
- **Modular Routers**: Discrete route modules grouped by functional domain under `app/routers/`.
- **Validation**: Strict input parsing and sanitization using Pydantic v2 schemas (`app/schemas/`).
- **Authorization & Security**:
  - PBKDF2-HMAC-SHA256 password hashing with 100,000 rounds and random salt.
  - Signed asymmetric/symmetric JWT access tokens (`HS256`).
  - Strict Role-Based Access Control (RBAC) enforced on every protected backend route via FastAPI dependency injection.
- **Audit Logging**: Structured auditing recorded on all authentication events, role changes, verification decisions, and job postings.

### 2.3 Data & Storage Layer
- **Relational ORM**: SQLAlchemy 2.0 ORM with connection pooling, declarative models, foreign keys, indexes, and constraints.
- **Zero-Setup Local Compatibility**: Default SQLite database (`cms_alumni.db`) for immediate offline execution, with seamless switchability to PostgreSQL in production via `DATABASE_URL`.
- **Separate File Storage**: Resumes (`media/resumes`), profile avatars (`media/avatars`), and technical documents (`media/resources`) stored outside database tables with extension and MIME-type validation.

---

## 3. User Roles & RBAC Matrix

| Feature / Resource | Student | Alumni | Faculty | Admin | Super Admin |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Alumni Directory** | View / Search | View / Search | View / Search | Full Manage | Full Manage |
| **Developer Portfolio** | Own Profile | Full Showcase | View / Guide | View / Manage | Full Manage |
| **Jobs & Internships** | View / Apply | Post / Review | View / Guide | Full Manage | Full Manage |
| **Internal Referrals** | Request Referral | Offer / Review | Monitor | Full Manage | Full Manage |
| **1-on-1 Mentorship** | Request | Offer / Schedule | Monitor | Full Manage | Full Manage |
| **Mock Interviews** | Book Slot | Conduct / Rate | View | Full Manage | Full Manage |
| **Resume Reviews** | Upload Resume | Critique / Advise | View | Full Manage | Full Manage |
| **Industry Projects** | Submit Proposal| Post Problem | Guide / Approve| Full Manage | Full Manage |
| **Resource Library** | Download | Upload / Share | Upload / Share | Full Manage | Full Manage |
| **Events & Hackathons** | Register / Hack | Judge / Speak | Organize | Full Manage | Full Manage |
| **Internal Messaging** | Protected 1-on-1| Protected 1-on-1| Protected 1-on-1| Moderation | Full Manage |
| **Account Verification**| Verify Request | Auto / Review | Approve | Full Manage | Full Manage |
| **Audit Logs & Roles** | No Access | No Access | No Access | Read Logs | Modify Roles |

---

## 4. Institutional Verification Workflow

To preserve the credibility of CMS Kanpur graduates, the platform executes a 2-step verification protocol:

```
                          User Registers (Roll No + Enrollment No)
                                             |
                                             v
                       Query AuthorizedCollegeRegistry Database
                                             |
                   +-------------------------+-------------------------+
                   |                                                   |
             Record Matches                                      No Direct Match
                   |                                                   |
                   v                                                   v
         Auto-Verified = TRUE                                Verification Status = PENDING
      Badge: "Verified CMS Alumnus"                                    |
      Granted Full Referral &                                 Admin Verification Queue
      Mentorship Privileges                                            |
                                                                       v
                                                        Admin Reviews College Records
                                                                       |
                                                      +----------------+----------------+
                                                      |                                 |
                                                  APPROVED                          REJECTED
                                                      |                                 |
                                             Auto-Verified = TRUE             Account Suspended/Flagged
```
