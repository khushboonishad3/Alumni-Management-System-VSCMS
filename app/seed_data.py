import os
from datetime import datetime, timezone, timedelta
from app.database import SessionLocal, Base, engine
from app.models import (
    User, UserRole, VerificationStatus, ProfileVisibility,
    AuthorizedCollegeRegistry, StudentProfile, AlumniProfile,
    AlumniProject, AlumniExperience,
    Job, JobType, LocationType, ApplicationStatus, ReferralStatus,
    JobApplication, ReferralRequest, SavedJob,
    MentorshipProfile, MentorshipRequest, MentorshipSession,
    MockInterview, ResumeReview, InterviewType, ReviewStatus,
    MentorshipStatus, SessionStatus,
    IndustryProject, ProjectProposal, ProjectMilestone, ProjectDifficulty, ProjectStatus, ProposalStatus,
    ResourceCategory, TechnicalResource,
    Event, EventRegistration, EventType, EventRole,
    Conversation, Message, Notification, Newsletter, NewsletterSubscriber,
    AuditLog
)
from app.core.security import hash_password

def seed_database():
    """Seeds the database with realistic CMS Kanpur BCA/MCA technical ecosystem data."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if already seeded
    if db.query(User).filter(User.email == "superadmin@cmskanpur.edu.in").first():
        print("Database already contains seed data.")
        db.close()
        return

    print("Seeding CMS Kanpur Alumni Management Database...")

    # 1. College Authorized Registry (Pre-authorized Roster)
    roster_entries = [
        AuthorizedCollegeRegistry(full_name="Aarav Sharma", enrollment_no="CMS2020MCA042", roll_no="20MCA042", course="MCA", batch_year=2020, graduation_year=2022, status="alumni", is_claimed=True),
        AuthorizedCollegeRegistry(full_name="Priya Verma", enrollment_no="CMS2019BCA015", roll_no="19BCA015", course="BCA", batch_year=2019, graduation_year=2022, status="alumni", is_claimed=True),
        AuthorizedCollegeRegistry(full_name="Rohan Gupta", enrollment_no="CMS2021MCA088", roll_no="21MCA088", course="MCA", batch_year=2021, graduation_year=2023, status="alumni", is_claimed=True),
        AuthorizedCollegeRegistry(full_name="Ananya Mishra", enrollment_no="CMS2020BCA009", roll_no="20BCA009", course="BCA", batch_year=2020, graduation_year=2023, status="alumni", is_claimed=True),
        AuthorizedCollegeRegistry(full_name="Vikram Singh", enrollment_no="CMS2018MCA031", roll_no="18MCA031", course="MCA", batch_year=2018, graduation_year=2020, status="alumni", is_claimed=True),
        AuthorizedCollegeRegistry(full_name="Sneha Dixit", enrollment_no="CMS2022MCA012", roll_no="22MCA012", course="MCA", batch_year=2022, graduation_year=2024, status="alumni", is_claimed=True),
        AuthorizedCollegeRegistry(full_name="Aditya Tiwari", enrollment_no="CMS2023BCA055", roll_no="23BCA055", course="BCA", batch_year=2023, graduation_year=2026, status="active", is_claimed=True),
        AuthorizedCollegeRegistry(full_name="Ritu Yadav", enrollment_no="CMS2023MCA021", roll_no="23MCA021", course="MCA", batch_year=2023, graduation_year=2025, status="active", is_claimed=True),
        # Unclaimed records for verification testing
        AuthorizedCollegeRegistry(full_name="Karan Malhotra", enrollment_no="CMS2022BCA077", roll_no="22BCA077", course="BCA", batch_year=2022, graduation_year=2025, status="active", is_claimed=False),
        AuthorizedCollegeRegistry(full_name="Deepika Pandey", enrollment_no="CMS2021BCA033", roll_no="21BCA033", course="BCA", batch_year=2021, graduation_year=2024, status="alumni", is_claimed=False),
    ]
    db.add_all(roster_entries)
    db.commit()

    # 2. Administrative and Faculty Users
    super_admin = User(
        email="superadmin@cmskanpur.edu.in",
        hashed_password=hash_password("Admin@CMS2025"),
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        is_verified=True
    )
    db.add(super_admin)
    db.flush()

    admin_user = User(
        email="admin@cmskanpur.edu.in",
        hashed_password=hash_password("Admin@CMS2025"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    db.add(admin_user)
    db.flush()

    faculty_user = User(
        email="faculty.cs@cmskanpur.edu.in",
        hashed_password=hash_password("Faculty@CMS2025"),
        role=UserRole.FACULTY,
        is_active=True,
        is_verified=True
    )
    db.add(faculty_user)
    db.flush()

    db.add(StudentProfile(
        user_id=faculty_user.id,
        full_name="Dr. R. K. Srivastava",
        enrollment_no="FACULTY-CS-01",
        roll_no="FAC01",
        course="MCA",
        batch_year=2010,
        bio="Head of Department, Computer Applications (BCA/MCA), CMS Kanpur. Passionate about industry-academia collaboration.",
        verification_status=VerificationStatus.VERIFIED
    ))

    # 3. Verified Alumni Users
    alumni_dataset = [
        {
            "email": "aarav.sharma@microsoft.com",
            "name": "Aarav Sharma",
            "enrollment": "CMS2020MCA042",
            "roll": "20MCA042",
            "course": "MCA",
            "batch": 2020,
            "grad": 2022,
            "company": "Microsoft",
            "title": "Senior Software Engineer",
            "city": "Hyderabad",
            "exp": 4.5,
            "skills": "C#, .NET Core, Azure, Distributed Systems, Microservices, SQL",
            "bio": "MCA 2022 alumnus. Building scalable cloud microservices at Microsoft Azure. Eager to mentor CMS Kanpur students in backend engineering and cloud architecture.",
            "github": "https://github.com/aarav-sharma-dev",
            "linkedin": "https://linkedin.com/in/aarav-sharma-cms",
            "leetcode": "https://leetcode.com/aarav_codes",
            "mentor_topics": "System Design, C#/.NET Core, Azure Cloud, Microsoft SDE Interview Prep"
        },
        {
            "email": "priya.verma@amazon.com",
            "name": "Priya Verma",
            "enrollment": "CMS2019BCA015",
            "roll": "19BCA015",
            "course": "BCA",
            "batch": 2019,
            "grad": 2022,
            "company": "Amazon",
            "title": "SDE-2 (AWS)",
            "city": "Bengaluru",
            "exp": 3.8,
            "skills": "Java, Spring Boot, AWS, DynamoDB, Docker, Kafka, DSA",
            "bio": "BCA 2022 graduate from CMS Kanpur. Currently working on AWS core services. Active mentor for DSA, algorithmic problem solving, and referral provider.",
            "github": "https://github.com/priyaverma-tech",
            "linkedin": "https://linkedin.com/in/priya-verma-aws",
            "leetcode": "https://leetcode.com/priya_dsa",
            "mentor_topics": "Data Structures & Algorithms, LeetCode 75, Java Spring Boot, Amazon SDE Interviews"
        },
        {
            "email": "rohan.gupta@zomato.com",
            "name": "Rohan Gupta",
            "enrollment": "CMS2021MCA088",
            "roll": "21MCA088",
            "course": "MCA",
            "batch": 2021,
            "grad": 2023,
            "company": "Zomato",
            "title": "Lead Full-Stack Engineer",
            "city": "Gurugram",
            "exp": 3.0,
            "skills": "Python, FastAPI, React, TypeScript, Redis, PostgreSQL, Docker",
            "bio": "CMS Kanpur MCA alumnus. Working on high-throughput backend services and interactive frontend systems. Love guiding final year capstone projects.",
            "github": "https://github.com/rohan-gupta-fs",
            "linkedin": "https://linkedin.com/in/rohan-gupta-zomato",
            "leetcode": "https://leetcode.com/rohan_dev",
            "mentor_topics": "Modern Full-Stack Development, FastAPI & React, Redis Caching, Startup Culture"
        },
        {
            "email": "ananya.mishra@paytm.com",
            "name": "Ananya Mishra",
            "enrollment": "CMS2020BCA009",
            "roll": "20BCA009",
            "course": "BCA",
            "batch": 2020,
            "grad": 2023,
            "company": "Paytm",
            "title": "Frontend Architect",
            "city": "Noida",
            "exp": 2.5,
            "skills": "JavaScript, TypeScript, React, Next.js, Redux Toolkit, TailwindCSS, Web Performance",
            "bio": "BCA 2023 batch. Focused on modern web interfaces, component libraries, and frontend performance optimization at Paytm Payments Bank.",
            "github": "https://github.com/ananya-m-ui",
            "linkedin": "https://linkedin.com/in/ananya-mishra-frontend",
            "leetcode": "https://leetcode.com/ananya_ui",
            "mentor_topics": "Modern React & Next.js, Frontend Architecture, Mock Technical Interviews"
        },
        {
            "email": "vikram.singh@tcs.com",
            "name": "Vikram Singh",
            "enrollment": "CMS2018MCA031",
            "roll": "18MCA031",
            "course": "MCA",
            "batch": 2018,
            "grad": 2020,
            "company": "TCS",
            "title": "Cloud DevOps Lead",
            "city": "Noida",
            "exp": 5.5,
            "skills": "DevOps, Kubernetes, Docker, Terraform, Jenkins, AWS, CI/CD, Linux",
            "bio": "MCA 2020 batch. Managing multi-region Kubernetes clusters and automated CI/CD pipelines. Actively providing referrals for TCS Digital and Ninja roles.",
            "github": "https://github.com/vikram-devops",
            "linkedin": "https://linkedin.com/in/vikram-singh-devops",
            "leetcode": "https://leetcode.com/vikram_s",
            "mentor_topics": "DevOps Career Track, Docker & Kubernetes Hands-on, TCS Digital Referrals"
        },
        {
            "email": "sneha.dixit@infosys.com",
            "name": "Sneha Dixit",
            "enrollment": "CMS2022MCA012",
            "roll": "22MCA012",
            "course": "MCA",
            "batch": 2022,
            "grad": 2024,
            "company": "Infosys",
            "title": "AI/ML Engineer",
            "city": "Pune",
            "exp": 1.5,
            "skills": "Python, PyTorch, Scikit-Learn, NLP, LLMs, GenAI, LangChain, FastAPI",
            "bio": "Recent MCA graduate. Working on generative AI and LLM orchestration workflows. Passionate about helping CMS juniors break into machine learning.",
            "github": "https://github.com/snehadixit-ai",
            "linkedin": "https://linkedin.com/in/sneha-dixit-ai",
            "leetcode": "https://leetcode.com/sneha_ml",
            "mentor_topics": "Machine Learning Foundations, PyTorch, GenAI Projects, Resume Reviews"
        }
    ]

    created_alumni = []
    for a in alumni_dataset:
        u = User(
            email=a["email"],
            hashed_password=hash_password("Alumni@CMS2025"),
            role=UserRole.ALUMNI,
            is_active=True,
            is_verified=True
        )
        db.add(u)
        db.flush()

        ap = AlumniProfile(
            user_id=u.id,
            full_name=a["name"],
            enrollment_no=a["enrollment"],
            roll_no=a["roll"],
            course=a["course"],
            batch_year=a["batch"],
            graduation_year=a["grad"],
            bio=a["bio"],
            current_company=a["company"],
            current_job_title=a["title"],
            industry="Information Technology & Software Services",
            years_of_experience=a["exp"],
            employment_type="Full-time",
            current_city=a["city"],
            country="India",
            skills=a["skills"],
            github_url=a["github"],
            linkedin_url=a["linkedin"],
            leetcode_url=a["leetcode"],
            is_mentor=True,
            is_referral_provider=True,
            is_co_guide=True,
            verification_status=VerificationStatus.VERIFIED,
            verification_notes="Verified via CMS Kanpur Official Alumni Record Roster."
        )
        db.add(ap)
        db.flush()

        # Add Projects for Alumni
        db.add(AlumniProject(
            alumni_id=ap.id,
            title="Enterprise Cloud Migration Platform",
            description="Designed and deployed microservices architecture handling 50k+ daily transactions with 99.99% uptime.",
            technologies="Docker, Kubernetes, AWS, PostgreSQL",
            github_url=a["github"],
            role="Lead Engineer",
            completion_year=2023
        ))

        # Add Experience
        db.add(AlumniExperience(
            alumni_id=ap.id,
            company=a["company"],
            job_title=a["title"],
            location=a["city"],
            start_date="June 2022",
            end_date="Present",
            is_current=True,
            description="Core engineering development, code reviews, and mentorship of junior engineers."
        ))

        # Add Mentorship Profile
        db.add(MentorshipProfile(
            alumni_id=ap.id,
            topics=a["mentor_topics"],
            bio=f"Open to guiding CMS Kanpur BCA & MCA students on {a['mentor_topics']}.",
            max_mentees=5,
            meeting_format="Google Meet / 1-on-1 Virtual",
            availability_details="Saturdays & Sundays (11:00 AM - 1:00 PM IST)",
            is_active=True
        ))

        created_alumni.append((u, ap))

    # 4. Student Users
    students_dataset = [
        {
            "email": "aditya.tiwari@cmskanpur.edu.in",
            "name": "Aditya Tiwari",
            "enrollment": "CMS2023BCA055",
            "roll": "23BCA055",
            "course": "BCA",
            "batch": 2023,
            "sem": 4,
            "cgpa": 8.7,
            "skills": "Python, Django, JavaScript, React, MySQL, Git",
            "bio": "4th Semester BCA student passionate about Python Web Development and competitive programming.",
            "github": "https://github.com/aditya-bca-cms",
            "linkedin": "https://linkedin.com/in/aditya-tiwari-cms",
            "leetcode": "https://leetcode.com/aditya_codes"
        },
        {
            "email": "ritu.yadav@cmskanpur.edu.in",
            "name": "Ritu Yadav",
            "enrollment": "CMS2023MCA021",
            "roll": "23MCA021",
            "course": "MCA",
            "batch": 2023,
            "sem": 3,
            "cgpa": 9.1,
            "skills": "Java, Spring Boot, PostgreSQL, Docker, Data Structures, Angular",
            "bio": "MCA 2nd year student. Preparing for SDE campus placements, solving LeetCode daily, looking for industry referrals.",
            "github": "https://github.com/ritu-yadav-dev",
            "linkedin": "https://linkedin.com/in/ritu-yadav-mca",
            "leetcode": "https://leetcode.com/ritu_algorithms"
        }
    ]

    created_students = []
    for s in students_dataset:
        u = User(
            email=s["email"],
            hashed_password=hash_password("Student@CMS2025"),
            role=UserRole.STUDENT,
            is_active=True,
            is_verified=True
        )
        db.add(u)
        db.flush()

        sp = StudentProfile(
            user_id=u.id,
            full_name=s["name"],
            enrollment_no=s["enrollment"],
            roll_no=s["roll"],
            course=s["course"],
            batch_year=s["batch"],
            current_semester=s["sem"],
            cgpa=s["cgpa"],
            bio=s["bio"],
            skills=s["skills"],
            github_url=s["github"],
            linkedin_url=s["linkedin"],
            leetcode_url=s["leetcode"],
            verification_status=VerificationStatus.VERIFIED,
            verification_notes="Verified via CMS Kanpur Official Enrollment Roster."
        )
        db.add(sp)
        created_students.append((u, sp))

    # Also add 1 pending student for admin verification workflow demo
    pending_student_user = User(
        email="rahul.verma@cmskanpur.edu.in",
        hashed_password=hash_password("Student@CMS2025"),
        role=UserRole.STUDENT,
        is_active=True,
        is_verified=False
    )
    db.add(pending_student_user)
    db.flush()
    db.add(StudentProfile(
        user_id=pending_student_user.id,
        full_name="Rahul Verma",
        enrollment_no="CMS2024BCA102",
        roll_no="24BCA102",
        course="BCA",
        batch_year=2024,
        current_semester=2,
        cgpa=8.0,
        skills="C++, Python, Web Basics",
        bio="1st year BCA student waiting for admin review.",
        verification_status=VerificationStatus.PENDING,
        verification_notes="Self-registered; awaiting administrator approval."
    ))

    db.commit()

    # 5. Resource Categories and Resources
    categories_data = [
        ("DSA & Competitive Programming", "dsa", "Data Structures, Algorithms, and LeetCode problem sets", "code"),
        ("System Design & Architecture", "system-design", "High Level & Low Level Design principles, Microservices, Caching", "cpu"),
        ("Web & Full Stack Development", "web-dev", "React, Next.js, FastAPI, Spring Boot, Node.js guides", "globe"),
        ("AI, ML & Data Science", "ai-ml", "Machine learning roadmaps, Python notebooks, and deep learning resources", "brain"),
        ("Cloud & DevOps", "devops", "Docker, Kubernetes, AWS, Terraform, and CI/CD cheat sheets", "cloud"),
        ("Placement & Interview Prep", "placement-prep", "Previous placement papers, HR interview questions, CMS placement guides", "briefcase"),
        ("Core Computer Science", "core-cs", "Operating Systems, DBMS, Computer Networks, and Theory of Computation", "database"),
        ("Resume Templates & Portfolios", "resume-templates", "ATS-compliant resume templates and developer portfolio guides", "file-text"),
    ]

    created_cats = {}
    for name, slug, desc, icon in categories_data:
        cat = ResourceCategory(name=name, slug=slug, description=desc, icon=icon)
        db.add(cat)
        db.flush()
        created_cats[slug] = cat

    # Add Technical Resources
    resources_dataset = [
        (
            "CMS Kanpur Complete DSA & LeetCode Roadmap (150 Questions)",
            "Curated by CMS Alumni at Microsoft and Amazon. Covers Arrays, Trees, Graphs, Dynamic Programming, and System Design basics with video solution links.",
            "PDF",
            "dsa",
            "https://drive.google.com/file/d/cms_dsa_150_roadmap/view",
            "DSA, LeetCode, Interview Prep, C++, Java, Python",
            142
        ),
        (
            "System Design Primer for BCA/MCA Campus Placements",
            "Comprehensive breakdown of Caching, Load Balancing, SQL vs NoSQL, Sharding, and Microservices design patterns with CMS alumni case studies.",
            "PDF",
            "system-design",
            "https://drive.google.com/file/d/cms_system_design_primer/view",
            "System Design, Scalability, Redis, Kafka, Microservices",
            98
        ),
        (
            "Production-Grade FastAPI + PostgreSQL Architecture Boilerplate",
            "Clean architecture template featuring JWT authentication, SQLAlchemy 2.0 ORM, Pydantic schemas, and Docker deployment configurations.",
            "CODE",
            "web-dev",
            "https://github.com/cms-kanpur-alumni/fastapi-production-boilerplate",
            "Python, FastAPI, PostgreSQL, Docker, Clean Architecture",
            85
        ),
        (
            "Top 50 DBMS & SQL Interview Questions with Solved Schema Scenarios",
            "Essential SQL queries (Joins, Subqueries, Indexing, Window functions) asked in TCS, Infosys, and Product company placement drives.",
            "PDF",
            "core-cs",
            "https://drive.google.com/file/d/cms_sql_interview_mastery/view",
            "DBMS, SQL, Normalization, Indexing, Transactions",
            120
        ),
        (
            "ATS-Friendly Software Engineer Resume Template (LaTeX & Word)",
            "Proven resume template tested by CMS Kanpur alumni who placed at Amazon, Microsoft, and Paytm. High parse rate on Taleo, Workday, and Greenhouse.",
            "DOC",
            "resume-templates",
            "https://drive.google.com/file/d/cms_ats_resume_template/view",
            "Resume, ATS, Career, SDE-1, Fresher",
            230
        )
    ]

    for title, desc, r_type, cat_slug, ext_link, tags, d_count in resources_dataset:
        db.add(TechnicalResource(
            uploader_id=created_alumni[0][0].id,
            category_id=created_cats[cat_slug].id,
            title=title,
            description=desc,
            resource_type=r_type,
            external_link=ext_link,
            tags=tags,
            downloads_count=d_count,
            is_approved=True
        ))

    # 6. Jobs & Internships
    jobs_dataset = [
        (
            created_alumni[0][0].id,
            "Software Development Engineer - 1 (Cloud Backend)",
            "Microsoft",
            JobType.FULL_TIME,
            LocationType.HYBRID,
            "Hyderabad, India",
            "0-2 Years",
            "18 - 26 LPA",
            "C#, .NET Core, Azure, Distributed Systems, SQL",
            "Looking for passionate BCA/MCA graduates from CMS Kanpur with strong foundations in object-oriented programming, data structures, and cloud architecture. Immediate internal referral available for shortlisted candidates!",
            "https://careers.microsoft.com/jobs",
            "2026-10-31",
            True
        ),
        (
            created_alumni[1][0].id,
            "AWS SDE Intern (6 Months / Pre-Placement Offer)",
            "Amazon",
            JobType.INTERNSHIP,
            LocationType.ON_SITE,
            "Bengaluru, India",
            "Fresher / Final Year",
            "Stipend: ₹80,000 / Month + PPO",
            "Java, Data Structures, Algorithms, OOP, AWS",
            "Amazon AWS team is hiring 6-month Software Development Engineer Interns from graduating BCA/MCA batches. High probability of PPO conversion based on performance.",
            "https://amazon.jobs",
            "2026-11-15",
            True
        ),
        (
            created_alumni[2][0].id,
            "Full-Stack Python & React Developer",
            "Zomato",
            JobType.FULL_TIME,
            LocationType.HYBRID,
            "Gurugram, India",
            "1-3 Years",
            "12 - 18 LPA",
            "Python, FastAPI, React, PostgreSQL, Docker, Redis",
            "Join our core consumer platform team building ultra low-latency APIs and snappy frontend experiences. Alumni referral available for CMS students with portfolio projects.",
            "https://zomato.com/careers",
            "2026-10-25",
            True
        ),
        (
            created_alumni[3][0].id,
            "Frontend Engineer (React / Next.js)",
            "Paytm",
            JobType.FULL_TIME,
            LocationType.ON_SITE,
            "Noida, India",
            "0-2 Years",
            "8 - 14 LPA",
            "JavaScript, TypeScript, React, Next.js, Redux, TailwindCSS",
            "We are looking for frontend wizards who care about 60fps animations, mobile-first responsiveness, and rock-solid state management.",
            "https://paytm.com/careers",
            "2026-11-05",
            True
        ),
        (
            created_alumni[4][0].id,
            "Cloud & DevOps Engineer (TCS Digital Track)",
            "TCS",
            JobType.FULL_TIME,
            LocationType.HYBRID,
            "Noida / Greater Noida",
            "0-1 Year",
            "7.5 - 9 LPA",
            "Linux, Docker, Kubernetes, CI/CD, AWS, Python scripting",
            "Direct referral drive for TCS Digital profile. Fresh BCA/MCA graduates with strong scripting and cloud fundamentals are encouraged to request referrals.",
            "https://tcs.com/careers",
            "2026-12-01",
            True
        )
    ]

    created_jobs = []
    for poster_id, title, comp, j_type, loc_type, loc, exp, sal, skills, desc, link, deadline, ref in jobs_dataset:
        j = Job(
            poster_id=poster_id,
            title=title,
            company=comp,
            job_type=j_type,
            location_type=loc_type,
            location=loc,
            experience_required=exp,
            salary_range=sal,
            required_skills=skills,
            description=desc,
            external_apply_url=link,
            deadline=deadline,
            is_referral_available=ref,
            is_active=True
        )
        db.add(j)
        db.flush()
        created_jobs.append(j)

    # 7. Referral Requests (Student -> Alumni)
    ref_req = ReferralRequest(
        job_id=created_jobs[0].id,
        alumni_id=created_alumni[0][0].id,
        student_id=created_students[1][0].id, # Ritu Yadav (MCA)
        target_company="Microsoft",
        target_role="Software Development Engineer - 1",
        resume_url="https://drive.google.com/file/d/ritu_yadav_mca_resume/view",
        note="Respected Aarav Sir, I am Ritu Yadav from MCA 3rd sem. I have solved 350+ LeetCode problems and built a distributed task queue in C# and SQL. I would be immensely grateful for your referral.",
        status=ReferralStatus.ACCEPTED,
        feedback="Resume looks solid! I have submitted your profile on Microsoft internal referral portal (Job ID #MS-9821). Expect an email from recruiter soon."
    )
    db.add(ref_req)

    # 8. Mentorship Requests & Sessions
    ment_req = MentorshipRequest(
        mentor_id=created_alumni[1][0].id, # Priya Verma (Amazon)
        mentee_id=created_students[0][0].id, # Aditya Tiwari (BCA)
        topic="Cracking Amazon SDE Internship as a BCA Student",
        message="Respected Priya Ma'am, I am in BCA 4th sem. I want guidance on building high-impact backend projects and structuring my DSA roadmap for Amazon campus evaluations.",
        status=MentorshipStatus.ACTIVE
    )
    db.add(ment_req)
    db.flush()

    # Mentorship session scheduled
    db.add(MentorshipSession(
        request_id=ment_req.id,
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=3, hours=4),
        duration_minutes=45,
        meeting_link="https://meet.google.com/cms-alumni-priya",
        agenda="Review current LeetCode progress, project architecture critique, and DSA priority topics.",
        status=SessionStatus.SCHEDULED
    ))

    # Mock Interview
    db.add(MockInterview(
        interviewer_id=created_alumni[2][0].id, # Rohan Gupta (Zomato)
        interviewee_id=created_students[1][0].id, # Ritu Yadav
        interview_type=InterviewType.TECHNICAL,
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=2),
        meeting_link="https://meet.google.com/cms-mock-interview",
        status="scheduled"
    ))

    # Resume Review
    db.add(ResumeReview(
        reviewer_id=created_alumni[3][0].id, # Ananya Mishra (Paytm)
        student_id=created_students[0][0].id, # Aditya Tiwari
        resume_url="https://drive.google.com/file/d/aditya_bca_resume/view",
        target_roles="Frontend Developer, Full-Stack Intern",
        status=ReviewStatus.COMPLETED,
        review_comments="Strong GitHub links! Recommend moving Skills section to top below contact details, and quantizing project achievements (e.g. reduced load time by 30%).",
        suggestions="Add deployed demo links for your 2 best React projects.",
        completed_at=datetime.now(timezone.utc) - timedelta(days=1)
    ))

    # 9. Industry Project Problem Statements & Proposals
    proj_problem = IndustryProject(
        creator_id=created_alumni[2][0].id, # Rohan Gupta (Zomato)
        faculty_id=faculty_user.id,
        title="Distributed Event-Driven Order Tracking & Webhook Engine",
        description="Build a high-throughput, fault-tolerant distributed webhook system that reliably delivers partner order notifications with exponential backoff retries, Redis idempotency keys, and metrics monitoring.",
        domain="Backend & Distributed Systems",
        required_technologies="Python, FastAPI, Redis, PostgreSQL, Docker, Prometheus",
        difficulty=ProjectDifficulty.ADVANCED,
        expected_outcome="Production-tested microservice with load testing reports handling 10,000 requests/second.",
        duration_weeks=10,
        max_students=4,
        status=ProjectStatus.APPROVED
    )
    db.add(proj_problem)
    db.flush()

    db.add(ProjectProposal(
        project_id=proj_problem.id,
        student_team_lead_id=created_students[1][0].id, # Ritu Yadav
        team_members="Ritu Yadav (23MCA021), Aditya Tiwari (23BCA055), Sneha Gupta (23MCA045)",
        proposal_text="Our team proposes building the event delivery pipeline using Celery/Redis queues, FastAPI endpoints, and a PostgreSQL auditing store. We will deploy using Docker Compose and demonstrate failover resilience.",
        status=ProposalStatus.ACCEPTED,
        feedback="Excellent architecture design. Project proposal approved for MCA 3rd semester capstone!"
    ))

    # 10. Technical Events & Hackathons
    now = datetime.now(timezone.utc)
    ev1 = Event(
        organizer_id=faculty_user.id,
        title="CMS Kanpur Smart Tech Hackathon 2026",
        event_type=EventType.HACKATHON,
        description="A 36-hour flagship technical hackathon for BCA and MCA students. Problem statements provided by CMS alumni working at top tier tech companies in FinTech, EdTech, Cloud, and Generative AI. Exciting cash prizes, internships, and mentorship guaranteed!",
        venue_or_link="CMS Kanpur Central Auditorium & Innovation Lab",
        is_online=False,
        start_time=now + timedelta(days=14),
        end_time=now + timedelta(days=16),
        capacity=200,
        speaker_info="Alumni Judges: Aarav Sharma (Microsoft), Priya Verma (Amazon), Rohan Gupta (Zomato)",
        is_published=True
    )
    db.add(ev1)
    db.flush()

    ev2 = Event(
        organizer_id=created_alumni[0][0].id,
        title="Masterclass: Cracking Tier-1 Tech Companies as BCA/MCA Graduates",
        event_type=EventType.WEBINAR,
        description="Live interactive masterclass hosted by CMS alumni at Microsoft, Amazon, and Paytm. Learn how to bridge syllabus knowledge with industry expectations, build resume-worthy side projects, and master LeetCode patterns.",
        venue_or_link="https://meet.google.com/cms-alumni-tier1-tech",
        is_online=True,
        start_time=now + timedelta(days=5, hours=3),
        end_time=now + timedelta(days=5, hours=5),
        capacity=300,
        speaker_info="Aarav Sharma (Microsoft) & Priya Verma (Amazon)",
        is_published=True
    )
    db.add(ev2)
    db.flush()

    # Event Registrations
    db.add(EventRegistration(event_id=ev1.id, user_id=created_students[0][0].id, role_in_event=EventRole.ATTENDEE))
    db.add(EventRegistration(event_id=ev1.id, user_id=created_students[1][0].id, role_in_event=EventRole.ATTENDEE))
    db.add(EventRegistration(event_id=ev1.id, user_id=created_alumni[0][0].id, role_in_event=EventRole.JUDGE))
    db.add(EventRegistration(event_id=ev2.id, user_id=created_students[0][0].id, role_in_event=EventRole.ATTENDEE))

    # 11. Communication & Messages
    conv = Conversation(participant1_id=created_students[1][0].id, participant2_id=created_alumni[0][0].id)
    db.add(conv)
    db.flush()

    db.add(Message(
        conversation_id=conv.id,
        sender_id=created_students[1][0].id,
        content="Hello Aarav Sir, thank you so much for accepting my referral request for the SDE-1 position at Microsoft!",
        is_read=True,
        created_at=now - timedelta(hours=5)
    ))
    db.add(Message(
        conversation_id=conv.id,
        sender_id=created_alumni[0][0].id,
        content="You are welcome Ritu! Your LeetCode profile and projects look great. Make sure to brush up on SQL indexes and thread concurrency before the technical screening.",
        is_read=True,
        created_at=now - timedelta(hours=3)
    ))

    # 12. Notifications
    db.add(Notification(
        user_id=created_students[1][0].id,
        title="Referral Request Accepted!",
        message="Aarav Sharma has accepted your referral request for Microsoft SDE-1.",
        notification_type="referral",
        link="/referrals",
        is_read=False
    ))
    db.add(Notification(
        user_id=created_students[0][0].id,
        title="Resume Review Published",
        message="Ananya Mishra has provided feedback on your resume.",
        notification_type="mentorship",
        link="/mentorship",
        is_read=False
    ))

    # 13. Newsletter
    db.add(Newsletter(
        title="CMS Alumni Quarterly Gazette - Fall 2026 Edition",
        content_html="<h2>Welcome to CMS TechAlumni Gazette</h2><p>Celebrating our BCA & MCA alumni placements at Microsoft, Amazon, and Zomato! Over 30 students referred this quarter.</p>",
        sent_by_id=admin_user.id,
        is_sent=True,
        sent_at=now - timedelta(days=2)
    ))

    # 14. Audit Logs
    db.add(AuditLog(user_id=super_admin.id, action="SYSTEM_INIT", entity_type="System", details="Initialized CMS Alumni Platform database schemas and institutional roster."))
    db.add(AuditLog(user_id=created_alumni[0][0].id, action="JOB_POSTED", entity_type="Job", entity_id=created_jobs[0].id, details="Posted Microsoft SDE-1 opportunity with internal referral."))

    db.commit()
    db.close()
    print("Seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
