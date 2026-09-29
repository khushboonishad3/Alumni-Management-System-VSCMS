# CMS Kanpur Alumni Platform - Database Schema & ER Diagram

## 1. Entity Relationship (ER) Diagram

```mermaid
erDiagram
    USERS ||--o| STUDENT_PROFILES : has
    USERS ||--o| ALUMNI_PROFILES : has
    USERS ||--o{ AUDIT_LOGS : generates
    USERS ||--o{ NOTIFICATIONS : receives
    USERS ||--o{ CONVERSATIONS : participates
    USERS ||--o{ JOBS : posts
    USERS ||--o{ JOB_APPLICATIONS : submits
    USERS ||--o{ REFERRAL_REQUESTS : requests_or_reviews
    USERS ||--o{ MENTORSHIP_REQUESTS : requests_or_mentors
    USERS ||--o{ INDUSTRY_PROJECTS : creates_or_guides
    USERS ||--o{ TECHNICAL_RESOURCES : uploads
    USERS ||--o{ EVENTS : organizes
    USERS ||--o{ EVENT_REGISTRATIONS : attends

    ALUMNI_PROFILES ||--o{ ALUMNI_PROJECTS : showcases
    ALUMNI_PROFILES ||--o{ ALUMNI_EXPERIENCES : contains
    ALUMNI_PROFILES ||--o| MENTORSHIP_PROFILES : configures

    JOBS ||--o{ JOB_APPLICATIONS : receives
    JOBS ||--o{ REFERRAL_REQUESTS : links_to
    JOBS ||--o{ SAVED_JOBS : bookmarked_in

    MENTORSHIP_REQUESTS ||--o{ MENTORSHIP_SESSIONS : schedules

    INDUSTRY_PROJECTS ||--o{ PROJECT_PROPOSALS : receives
    INDUSTRY_PROJECTS ||--o{ PROJECT_MILESTONES : tracks

    RESOURCE_CATEGORIES ||--o{ TECHNICAL_RESOURCES : classifies

    EVENTS ||--o{ EVENT_REGISTRATIONS : records

    CONVERSATIONS ||--o{ MESSAGES : contains

    USERS {
        int id PK
        string email UK
        string hashed_password
        enum role
        bool is_active
        bool is_verified
        datetime created_at
        datetime updated_at
    }

    AUTHORIZED_COLLEGE_REGISTRY {
        int id PK
        string full_name
        string enrollment_no UK
        string roll_no UK
        string course
        int batch_year
        int graduation_year
        string status
        bool is_claimed
        datetime created_at
    }

    STUDENT_PROFILES {
        int id PK
        int user_id FK,UK
        string full_name
        string enrollment_no
        string roll_no
        string course
        int batch_year
        int current_semester
        float cgpa
        string phone
        text bio
        string avatar_url
        string resume_url
        string github_url
        string linkedin_url
        string leetcode_url
        string portfolio_url
        text skills
        enum verification_status
        text verification_notes
        bool show_email
        bool show_phone
    }

    ALUMNI_PROFILES {
        int id PK
        int user_id FK,UK
        string full_name
        string enrollment_no
        string roll_no
        string course
        int batch_year
        int graduation_year
        text bio
        string avatar_url
        string phone
        string current_company
        string current_job_title
        string industry
        float years_of_experience
        string employment_type
        string current_city
        string country
        string github_url
        string linkedin_url
        string leetcode_url
        string kaggle_url
        string hackerrank_url
        string stackoverflow_url
        string portfolio_url
        text skills
        bool is_mentor
        bool is_referral_provider
        bool is_co_guide
        enum verification_status
        text verification_notes
        enum profile_visibility
        bool show_email
        bool show_phone
        datetime created_at
    }

    JOBS {
        int id PK
        int poster_id FK
        string title
        string company
        enum job_type
        enum location_type
        string location
        string experience_required
        string salary_range
        string required_skills
        text description
        string external_apply_url
        string deadline
        bool is_referral_available
        bool is_active
        datetime created_at
    }

    REFERRAL_REQUESTS {
        int id PK
        int job_id FK
        int alumni_id FK
        int student_id FK
        string target_company
        string target_role
        string resume_url
        text note
        enum status
        text feedback
        datetime created_at
        datetime updated_at
    }

    MENTORSHIP_REQUESTS {
        int id PK
        int mentor_id FK
        int mentee_id FK
        string topic
        text message
        enum status
        datetime created_at
        datetime updated_at
    }

    INDUSTRY_PROJECTS {
        int id PK
        int creator_id FK
        int faculty_id FK
        string title
        text description
        string domain
        string required_technologies
        enum difficulty
        text expected_outcome
        int duration_weeks
        int max_students
        enum status
        datetime created_at
    }

    TECHNICAL_RESOURCES {
        int id PK
        int uploader_id FK
        int category_id FK
        string title
        text description
        string resource_type
        string file_url
        string external_link
        string tags
        int downloads_count
        bool is_approved
        datetime created_at
    }

    EVENTS {
        int id PK
        int organizer_id FK
        string title
        enum event_type
        text description
        string venue_or_link
        bool is_online
        datetime start_time
        datetime end_time
        int capacity
        string speaker_info
        bool is_published
        datetime created_at
    }
```

---

## 2. Table Specifications & Indexes

### 2.1 `users`
- **Primary Key**: `id` (Auto-increment integer)
- **Indexes**:
  - `idx_users_email` (UNIQUE): Fast login lookup
  - `idx_users_role`: Fast RBAC filtering
  - `idx_users_verified`: Quick status filtering

### 2.2 `authorized_college_registry`
- **Primary Key**: `id`
- **Indexes**:
  - `idx_registry_enrollment` (UNIQUE): Prevents duplicate college registrations
  - `idx_registry_roll` (UNIQUE): Rapid enrollment verification

### 2.3 `alumni_profiles`
- **Primary Key**: `id`
- **Foreign Key**: `user_id` -> `users.id` (ON DELETE CASCADE)
- **Indexes**:
  - `idx_alumni_course_batch`: Accelerated multi-year batch filtering (e.g. `MCA 2020-2024`)
  - `idx_alumni_company`: Quick company cluster aggregations
  - `idx_alumni_mentor`: Instant filter for available mentors
  - `idx_alumni_referral`: Instant filter for referral providers

### 2.4 `jobs`
- **Primary Key**: `id`
- **Foreign Key**: `poster_id` -> `users.id`
- **Indexes**:
  - `idx_jobs_active_type`: Quick filtering of active full-time jobs vs internships
  - `idx_jobs_company`: Rapid search by hiring entity

### 2.5 `referral_requests`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `alumni_id` -> `users.id`
  - `student_id` -> `users.id`
  - `job_id` -> `jobs.id`
- **Status State Machine**:
  `REQUESTED` -> `UNDER_REVIEW` -> `ACCEPTED` / `REJECTED` -> `REFERRED` -> `INTERVIEW` -> `SELECTED` -> `CLOSED`
