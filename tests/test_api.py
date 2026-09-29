import pytest
from starlette.testclient import TestClient
from main import app
from app.core.security import hash_password, verify_password

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "CMS Kanpur" in data["college"]

def test_password_hashing():
    raw = "SecureSecret123!"
    hashed = hash_password(raw)
    assert verify_password(raw, hashed)
    assert not verify_password("WrongPassword", hashed)

def test_login_successful():
    response = client.post("/api/auth/login", json={
        "email": "aarav.sharma@microsoft.com",
        "password": "Alumni@CMS2025"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "alumni"
    assert data["is_verified"] is True
    assert data["full_name"] == "Aarav Sharma"

def test_login_invalid_password():
    response = client.post("/api/auth/login", json={
        "email": "aarav.sharma@microsoft.com",
        "password": "InvalidPassword"
    })
    assert response.status_code == 401

def test_registration_with_auto_verification():
    import time
    unique_ts = int(time.time() * 1000)
    response = client.post("/api/auth/register", json={
        "email": f"karan.test.{unique_ts}@cmskanpur.edu.in",
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
    })
    assert response.status_code == 200
    data = response.json()
    assert data["is_verified"] is True
    assert data["verification_status"] == "verified"
    assert "access_token" in data

def test_unauthenticated_alumni_access_denied():
    # Strict privacy: without an account you cannot access any information about the alumni
    anon_client = TestClient(app)
    res = anon_client.get("/api/alumni")
    assert res.status_code == 401
    assert res.json()["detail"] == "Could not validate credentials or session expired."

    res_detail = anon_client.get("/api/alumni/1")
    assert res_detail.status_code == 401

def test_alumni_directory_search():
    login_res = client.post("/api/auth/login", json={
        "email": "aarav.sharma@microsoft.com",
        "password": "Alumni@CMS2025"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Filter by course: MCA
    res_mca = client.get("/api/alumni?course=MCA", headers=headers)
    assert res_mca.status_code == 200
    data = res_mca.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["course"] == "MCA"

    # Filter by tech skill: Python
    res_tech = client.get("/api/alumni?technology=Python", headers=headers)
    assert res_tech.status_code == 200
    assert res_tech.json()["total"] >= 1

    # Filter by mentorship
    res_mentor = client.get("/api/alumni?mentorship=true", headers=headers)
    assert res_mentor.status_code == 200
    assert res_mentor.json()["total"] >= 1

def test_alumni_detail_privacy():
    login_res = client.post("/api/auth/login", json={
        "email": "aarav.sharma@microsoft.com",
        "password": "Alumni@CMS2025"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/alumni/1", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "full_name" in data
    assert "projects" in data
    assert "experiences" in data

def test_jobs_list_and_details():
    res = client.get("/api/jobs")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    job_id = data["items"][0]["id"]
    
    # Detail
    res_detail = client.get(f"/api/jobs/{job_id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["id"] == job_id

def test_mentorship_mentors_list():
    res = client.get("/api/mentorship/mentors")
    assert res.status_code == 200
    mentors = res.json()
    assert len(mentors) >= 1
    assert "topics" in mentors[0]
    assert "full_name" in mentors[0]

def test_industry_projects():
    res = client.get("/api/projects")
    assert res.status_code == 200
    projects = res.json()
    assert len(projects) >= 1
    assert "required_technologies" in projects[0]

def test_technical_resources():
    res_cats = client.get("/api/resources/categories")
    assert res_cats.status_code == 200
    cats = res_cats.json()
    assert len(cats) >= 5

    res_items = client.get("/api/resources")
    assert res_items.status_code == 200
    assert len(res_items.json()) >= 1

def test_events_list():
    res = client.get("/api/events")
    assert res.status_code == 200
    events = res.json()
    assert len(events) >= 1
    assert any(e["event_type"] == "hackathon" for e in events)

def test_global_search():
    res = client.get("/api/search?q=Python")
    assert res.status_code == 200
    data = res.json()
    assert data["total_hits"] >= 1
    assert "alumni" in data["results"]
    assert "jobs" in data["results"]

def test_admin_dashboard_metrics():
    # Login as admin
    login_res = client.post("/api/auth/login", json={
        "email": "admin@cmskanpur.edu.in",
        "password": "Admin@CMS2025"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.get("/api/admin/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert data["metrics"]["total_alumni"] >= 6
    assert data["metrics"]["total_students"] >= 2
    assert "charts" in data
    assert len(data["charts"]["batch_distribution"]) >= 1

def test_unauthorized_admin_access():
    # Fresh unauthenticated client without cookie session
    unauth_client = TestClient(app)
    res = unauth_client.get("/api/admin/dashboard")
    assert res.status_code == 401

    # Student trying to access admin dashboard
    stu_login = unauth_client.post("/api/auth/login", json={
        "email": "aditya.tiwari@cmskanpur.edu.in",
        "password": "Student@CMS2025"
    })
    stu_token = stu_login.json()["access_token"]
    res_stu = unauth_client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {stu_token}"})
    assert res_stu.status_code == 403

def test_captcha_generation_and_validation():
    # 1. Generate captcha
    res = client.get("/api/auth/captcha")
    assert res.status_code == 200
    data = res.json()
    assert "captcha_id" in data
    assert "captcha_svg" in data
    assert "<svg" in data["captcha_svg"]

    # 2. Login with invalid captcha
    res_bad = client.post("/api/auth/login", json={
        "email": "aarav.sharma@microsoft.com",
        "password": "Alumni@CMS2025",
        "captcha_id": data["captcha_id"],
        "captcha_code": "WRONG"
    })
    assert res_bad.status_code == 400
    assert "Captcha verification failed" in res_bad.json()["detail"]

def test_forgot_password_flow():
    res = client.post("/api/auth/forgot-password", json={
        "email": "aarav.sharma@microsoft.com"
    })
    assert res.status_code == 200
    data = res.json()
    assert "CMS AlumniConnect" in data["message"]
    assert data["simulated_reset_code"] == "CMS-2025"
