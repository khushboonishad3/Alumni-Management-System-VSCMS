# CMS Kanpur Alumni Platform - API Architecture & Specification

All API endpoints follow RESTful conventions, accept JSON payloads (or multipart/form-data for file uploads), and return standardized JSON responses.

Base URL: `http://localhost:8000/api`

---

## 1. Authentication Endpoints (`/api/auth`)

### 1.1 User Registration
- **URL**: `POST /api/auth/register`
- **Auth**: None (Public)
- **Description**: Registers a student or alumnus. Validates `enrollment_no` and `roll_no` against `authorized_college_registry`. If matched, sets status to `verified` immediately. Otherwise sets to `pending`.
- **Request Body**:
```json
{
  "email": "karan.malhotra@test.edu",
  "password": "Password123!",
  "role": "alumni",
  "full_name": "Karan Malhotra",
  "enrollment_no": "CMS2022BCA077",
  "roll_no": "22BCA077",
  "course": "BCA",
  "batch_year": 2022,
  "graduation_year": 2025,
  "current_company": "Infosys",
  "current_job_title": "Systems Engineer",
  "skills": "Java, Spring Boot, MySQL"
}
```
- **Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR...",
  "token_type": "bearer",
  "user_id": 14,
  "email": "karan.malhotra@test.edu",
  "role": "alumni",
  "full_name": "Karan Malhotra",
  "is_verified": true,
  "verification_status": "verified"
}
```

### 1.2 User Login
- **URL**: `POST /api/auth/login`
- **Auth**: None (Public)
- **Request Body**:
```json
{
  "email": "aarav.sharma@microsoft.com",
  "password": "Alumni@CMS2025"
}
```
- **Response (200 OK)**: Returns JWT access token and session cookie.

### 1.3 Current User Profile
- **URL**: `GET /api/auth/me`
- **Auth**: Bearer Token
- **Response (200 OK)**: Returns user record and nested role-specific profile.

---

## 2. Alumni Directory Endpoints (`/api/alumni`)

### 2.1 Search & Filter Alumni Directory
- **URL**: `GET /api/alumni`
- **Auth**: Optional (Unauthenticated requests view public profiles only)
- **Query Parameters**:
  - `q` (string): Keyword search across name, company, title, skills
  - `course` (string): `BCA` or `MCA`
  - `batch_from` / `batch_to` (integer): Filter graduation cohorts (e.g. `2020` - `2024`)
  - `technology` (string): Filter by technical skill tag (e.g. `Python`, `React`, `AWS`)
  - `company` (string): Filter by current employer (e.g. `Microsoft`, `Amazon`)
  - `mentorship` (boolean): `true` to show available mentors
  - `referral` (boolean): `true` to show alumni offering internal job referrals
  - `page` / `page_size` (integer): Pagination controls
- **Response (200 OK)**:
```json
{
  "total": 6,
  "page": 1,
  "page_size": 12,
  "total_pages": 1,
  "items": [
    {
      "id": 1,
      "user_id": 4,
      "full_name": "Aarav Sharma",
      "course": "MCA",
      "batch_year": 2020,
      "graduation_year": 2022,
      "current_company": "Microsoft",
      "current_job_title": "Senior Software Engineer",
      "current_city": "Hyderabad",
      "skills": ["C#", ".NET Core", "Azure", "Distributed Systems", "SQL"],
      "is_mentor": true,
      "is_referral_provider": true,
      "is_verified": true,
      "github_url": "https://github.com/aarav-sharma-dev",
      "linkedin_url": "https://linkedin.com/in/aarav-sharma-cms"
    }
  ]
}
```

### 2.2 Alumni Profile Detail
- **URL**: `GET /api/alumni/{id}`
- **Auth**: Optional
- **Response**: Full profile including career history (`experiences`), showcase portfolio (`projects`), and mentorship offering details.

---

## 3. Career & Referral Hub Endpoints (`/api/jobs`, `/api/referrals`)

### 3.1 List Jobs & Internships
- **URL**: `GET /api/jobs`
- **Query Parameters**: `q`, `job_type`, `location_type`, `referral_only`, `skills`
- **Response**: List of active career opportunities.

### 3.2 Apply to Job
- **URL**: `POST /api/jobs/{id}/apply`
- **Auth**: Bearer Token
- **Request Body**:
```json
{
  "resume_url": "https://drive.google.com/file/d/my_resume/view",
  "cover_note": "Application note highlighting LeetCode rating and projects."
}
```

### 3.3 Request Alumni Referral
- **URL**: `POST /api/referrals/request`
- **Auth**: Bearer Token (Student)
- **Request Body**:
```json
{
  "alumni_id": 4,
  "job_id": 1,
  "target_company": "Microsoft",
  "target_role": "Software Development Engineer - 1",
  "resume_url": "https://drive.google.com/file/d/resume/view",
  "note": "Requesting referral for SDE-1 opening."
}
```

### 3.4 Update Referral Status
- **URL**: `PUT /api/referrals/{id}/status`
- **Auth**: Bearer Token (Alumni / Admin)
- **Request Body**:
```json
{
  "status": "accepted",
  "feedback": "Submitted profile on Microsoft internal referral portal. Job ID #MS-9821."
}
```

---

## 4. Mentorship & Mock Interviews (`/api/mentorship`)

### 4.1 List Available Mentors
- **URL**: `GET /api/mentorship/mentors`
- **Response**: List of alumni mentors with topics, bio, and availability.

### 4.2 Send Mentorship Request
- **URL**: `POST /api/mentorship/requests`
- **Request Body**:
```json
{
  "mentor_id": 5,
  "topic": "Cracking Amazon SDE Internship as a BCA Student",
  "message": "Seeking guidance on backend projects and DSA roadmap."
}
```

### 4.3 Schedule Mentorship Session
- **URL**: `POST /api/mentorship/sessions?request_id={id}`
- **Request Body**:
```json
{
  "scheduled_at": "2026-10-05T11:00:00Z",
  "duration_minutes": 45,
  "meeting_link": "https://meet.google.com/cms-alumni-priya",
  "agenda": "Review LeetCode progress and project architecture critique."
}
```

---

## 5. Administration & Institutional Verification (`/api/admin`)

### 5.1 Analytics Dashboard Metrics
- **URL**: `GET /api/admin/dashboard`
- **Auth**: Bearer Token (Admin / Super Admin / Faculty)
- **Response**: Live counts and aggregated charts for batch distribution, company breakdown, and skill distribution.

### 5.2 Verification Queue
- **URL**: `GET /api/admin/verifications`
- **Auth**: Bearer Token (Admin / Faculty)
- **Response**: List of pending student and alumni registrations.

### 5.3 Approve or Reject Verification
- **URL**: `PUT /api/admin/verifications/{profile_id}?user_type=alumni`
- **Request Body**:
```json
{
  "status": "verified",
  "notes": "Verified against official CMS Kanpur MCA 2022 convocation list."
}
```
