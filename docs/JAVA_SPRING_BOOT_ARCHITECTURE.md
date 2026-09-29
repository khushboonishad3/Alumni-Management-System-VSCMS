# Java Spring Boot Compatibility Architecture Guide

## 1. Overview & Architectural Mapping

The CMS Kanpur Alumni Management Platform backend has been engineered with a clean, decoupled layer architecture. This document outlines how the Python FastAPI implementation maps directly into **Java 21 + Spring Boot 3.3** using Spring Data JPA, Spring Security 6, and Hibernate without altering the relational database schema or frontend API contracts.

```
Python FastAPI Layer                    Java Spring Boot Layer
--------------------                    ----------------------
app/routers/auth.py            --->     com.cms.alumni.controller.AuthController
app/routers/users.py           --->     com.cms.alumni.controller.AlumniController
app/routers/jobs.py            --->     com.cms.alumni.controller.JobController
app/routers/mentorship.py      --->     com.cms.alumni.controller.MentorshipController
app/routers/admin.py           --->     com.cms.alumni.controller.AdminController
app/models/*.py                --->     com.cms.alumni.entity.* (JPA Entities)
app/schemas/*.py               --->     com.cms.alumni.dto.* (Java Records / DTOs)
app/core/security.py           --->     com.cms.alumni.security.JwtService
app/core/dependencies.py       --->     com.cms.alumni.security.JwtAuthenticationFilter
```

---

## 2. Spring Boot Project Structure

```
src/main/java/com/cms/alumni/
├── config/
│   ├── SecurityConfig.java            # Spring Security 6 & JWT Filter chain
│   ├── CorsConfig.java                # CORS origins for frontend
│   └── WebConfig.java                 # Static and Media file handlers
├── controller/
│   ├── AuthController.java            # /api/auth
│   ├── AlumniController.java          # /api/alumni
│   ├── JobController.java             # /api/jobs & /api/referrals
│   ├── MentorshipController.java      # /api/mentorship
│   ├── ProjectController.java         # /api/projects
│   ├── ResourceController.java        # /api/resources
│   ├── EventController.java           # /api/events
│   ├── CommunicationController.java   # /api/messages & notifications
│   └── AdminController.java           # /api/admin
├── dto/
│   ├── request/                       # LoginRequest, RegisterRequest, etc.
│   └── response/                      # TokenResponse, AlumniDto, etc.
├── entity/
│   ├── User.java
│   ├── AuthorizedCollegeRegistry.java
│   ├── StudentProfile.java
│   ├── AlumniProfile.java
│   ├── Job.java
│   ├── ReferralRequest.java
│   ├── MentorshipProfile.java
│   ├── IndustryProject.java
│   └── AuditLog.java
├── repository/
│   ├── UserRepository.java
│   ├── AuthorizedCollegeRegistryRepository.java
│   ├── AlumniProfileRepository.java
│   ├── JobRepository.java
│   └── ReferralRequestRepository.java
├── service/
│   ├── AuthService.java
│   ├── AlumniService.java
│   ├── PlacementService.java
│   ├── MentorshipService.java
│   └── AdminService.java
└── security/
    ├── JwtService.java
    ├── JwtAuthenticationFilter.java
    └── UserDetailsServiceImpl.java
```

---

## 3. Entity Mapping Example (`AlumniProfile.java`)

```java
package com.cms.alumni.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "alumni_profiles", indexes = {
    @Index(name = "idx_alumni_course_batch", columnList = "course, batch_year"),
    @Index(name = "idx_alumni_company", columnList = "current_company")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AlumniProfile {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private User user;

    @Column(name = "full_name", nullable = false, length = 150)
    private String fullName;

    @Column(name = "enrollment_no", length = 50)
    private String enrollmentNo;

    @Column(name = "roll_no", length = 50)
    private String rollNo;

    @Column(name = "course", nullable = false, length = 20)
    private String course; // BCA or MCA

    @Column(name = "batch_year", nullable = false)
    private Integer batchYear;

    @Column(name = "graduation_year", nullable = false)
    private Integer graduationYear;

    @Column(name = "current_company", length = 150)
    private String currentCompany;

    @Column(name = "current_job_title", length = 150)
    private String currentJobTitle;

    @Column(columnDefinition = "TEXT")
    private String skills;

    @Column(name = "is_mentor")
    private Boolean isMentor = true;

    @Column(name = "is_referral_provider")
    private Boolean isReferralProvider = true;

    @Enumerated(EnumType.STRING)
    @Column(name = "verification_status")
    private VerificationStatus verificationStatus = VerificationStatus.PENDING;

    @OneToMany(mappedBy = "alumni", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<AlumniProject> projects;
}
```

---

## 4. Repository & Specifications for Multi-Filter Search

```java
package com.cms.alumni.repository;

import com.cms.alumni.entity.AlumniProfile;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.stereotype.Repository;

@Repository
public interface AlumniProfileRepository extends JpaRepository<AlumniProfile, Long>, JpaSpecificationExecutor<AlumniProfile> {
}
```

---

## 5. REST Controller Example (`AlumniController.java`)

```java
package com.cms.alumni.controller;

import com.cms.alumni.dto.response.AlumniDetailDto;
import com.cms.alumni.dto.response.PageResponse;
import com.cms.alumni.service.AlumniService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/alumni")
@RequiredArgsConstructor
public class AlumniController {

    private final AlumniService alumniService;

    @GetMapping
    public ResponseEntity<PageResponse<AlumniDetailDto>> getAlumni(
            @RequestParam(required = false) String q,
            @RequestParam(required = false) String course,
            @RequestParam(required = false) String technology,
            @RequestParam(required = false) String company,
            @RequestParam(required = false) Boolean mentorship,
            @RequestParam(required = false) Boolean referral,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "12") int pageSize) {
        
        return ResponseEntity.ok(alumniService.searchAlumni(q, course, technology, company, mentorship, referral, page, pageSize));
    }

    @GetMapping("/{id}")
    public ResponseEntity<AlumniDetailDto> getAlumniDetail(@PathVariable Long id) {
        return ResponseEntity.ok(alumniService.getAlumniById(id));
    }
}
```

---

## 6. Spring Security 6 JWT Filter Integration

In `SecurityConfig.java`, authenticate stateless bearer tokens:
```java
@Bean
public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    return http
        .csrf(AbstractHttpConfigurer::disable)
        .cors(Customizer.withDefaults())
        .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/api/auth/**", "/api/alumni/**", "/api/jobs/**", "/api/resources/**", "/api/search/**", "/static/**", "/media/**", "/", "/health").permitAll()
            .requestMatchers("/api/admin/**").hasAnyRole("ADMIN", "SUPER_ADMIN", "FACULTY")
            .anyRequest().authenticated()
        )
        .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class)
        .build();
}
```
