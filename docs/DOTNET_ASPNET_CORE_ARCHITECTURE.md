# C# .NET / ASP.NET Core Compatibility Architecture Guide

## 1. Overview & Architectural Mapping

The CMS Kanpur Alumni Platform backend can be hosted using **C# 12 and ASP.NET Core 8 (.NET 8/9)**. By utilizing Entity Framework Core (EF Core 8), ASP.NET Core Identity/JWT Bearer authentication, and standard REST controllers, the system can replace the Python API with zero frontend adjustments.

```
Python FastAPI Layer                    .NET / ASP.NET Core Layer
--------------------                    -------------------------
app/routers/auth.py            --->     Controllers/AuthController.cs
app/routers/users.py           --->     Controllers/AlumniController.cs
app/routers/jobs.py            --->     Controllers/JobsController.cs
app/routers/mentorship.py      --->     Controllers/MentorshipController.cs
app/routers/admin.py           --->     Controllers/AdminController.cs
app/models/*.py                --->     Models/*.cs (EF Core Entities)
app/database.py                --->     Data/CmsAlumniDbContext.cs
app/core/dependencies.py       --->     Authorization/RoleRequirementHandler.cs
```

---

## 2. Solution Structure

```
CmsAlumni.Api/
├── Controllers/
│   ├── AuthController.cs
│   ├── AlumniController.cs
│   ├── JobsController.cs
│   ├── MentorshipController.cs
│   ├── ProjectsController.cs
│   ├── ResourcesController.cs
│   ├── EventsController.cs
│   └── AdminController.cs
├── Data/
│   ├── CmsAlumniDbContext.cs          # EF Core DbContext with Fluent API mappings
│   └── DbInitializer.cs               # Seed data for CMS Kanpur
├── Models/
│   ├── User.cs
│   ├── AuthorizedCollegeRegistry.cs
│   ├── StudentProfile.cs
│   ├── AlumniProfile.cs
│   ├── Job.cs
│   ├── ReferralRequest.cs
│   ├── MentorshipProfile.cs
│   └── AuditLog.cs
├── DTOs/
│   ├── AuthDtos.cs                    # LoginDto, RegisterDto, TokenResponseDto
│   ├── AlumniDtos.cs                  # AlumniListDto, AlumniDetailDto
│   └── JobDtos.cs
├── Services/
│   ├── ITokenService.cs & TokenService.cs
│   ├── IAlumniService.cs & AlumniService.cs
│   └── IVerificationService.cs
└── Program.cs                         # Dependency Injection, Middleware, JWT Config
```

---

## 3. Entity Framework Core DbContext (`CmsAlumniDbContext.cs`)

```csharp
using Microsoft.EntityFrameworkCore;
using CmsAlumni.Api.Models;

namespace CmsAlumni.Api.Data;

public class CmsAlumniDbContext : DbContext
{
    public CmsAlumniDbContext(DbContextOptions<CmsAlumniDbContext> options) : base(options) {}

    public DbSet<User> Users => Set<User>();
    public DbSet<AuthorizedCollegeRegistry> CollegeRegistry => Set<AuthorizedCollegeRegistry>();
    public DbSet<StudentProfile> StudentProfiles => Set<StudentProfile>();
    public DbSet<AlumniProfile> AlumniProfiles => Set<AlumniProfile>();
    public DbSet<Job> Jobs => Set<Job>();
    public DbSet<JobApplication> JobApplications => Set<JobApplication>();
    public DbSet<ReferralRequest> ReferralRequests => Set<ReferralRequest>();
    public DbSet<MentorshipProfile> MentorshipProfiles => Set<MentorshipProfile>();
    public DbSet<IndustryProject> IndustryProjects => Set<IndustryProject>();
    public DbSet<TechnicalResource> TechnicalResources => Set<TechnicalResource>();
    public DbSet<Event> Events => Set<Event>();
    public DbSet<AuditLog> AuditLogs => Set<AuditLog>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<User>(entity =>
        {
            entity.HasIndex(u => u.Email).IsUnique();
        });

        modelBuilder.Entity<AuthorizedCollegeRegistry>(entity =>
        {
            entity.HasIndex(r => r.EnrollmentNo).IsUnique();
            entity.HasIndex(r => r.RollNo).IsUnique();
        });

        modelBuilder.Entity<AlumniProfile>(entity =>
        {
            entity.HasIndex(a => new { a.Course, a.BatchYear });
            entity.HasIndex(a => a.CurrentCompany);
        });
    }
}
```

---

## 4. REST Controller Implementation (`AlumniController.cs`)

```csharp
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using CmsAlumni.Api.Data;
using CmsAlumni.Api.DTOs;

namespace CmsAlumni.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AlumniController : ControllerBase
{
    private final CmsAlumniDbContext _context;

    public AlumniController(CmsAlumniDbContext context)
    {
        _context = context;
    }

    [HttpGet]
    public async Task<IActionResult> GetAlumni(
        [FromQuery] string? q,
        [FromQuery] string? course,
        [FromQuery] string? technology,
        [FromQuery] string? company,
        [FromQuery] bool? mentorship,
        [FromQuery] bool? referral,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 12)
    {
        var query = _context.AlumniProfiles
            .Include(a => a.User)
            .Where(a => a.User.IsActive);

        if (!string.IsNullOrWhiteSpace(q))
        {
            var term = $"%{q.Trim()}%";
            query = query.Where(a => EF.Functions.Like(a.FullName, term) ||
                                     EF.Functions.Like(a.CurrentCompany, term) ||
                                     EF.Functions.Like(a.CurrentJobTitle, term) ||
                                     EF.Functions.Like(a.Skills, term));
        }

        if (!string.IsNullOrWhiteSpace(course))
            query = query.Where(a => a.Course == course.ToUpper());

        if (!string.IsNullOrWhiteSpace(technology))
            query = query.Where(a => EF.Functions.Like(a.Skills, $"%{technology.Trim()}%"));

        if (mentorship.HasValue)
            query = query.Where(a => a.IsMentor == mentorship.Value);

        if (referral.HasValue)
            query = query.Where(a => a.IsReferralProvider == referral.Value);

        var total = await query.CountAsync();
        var items = await query
            .OrderByDescending(a => a.BatchYear)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(a => new AlumniListDto(
                a.Id, a.UserId, a.FullName, a.Course, a.BatchYear, a.GraduationYear,
                a.CurrentCompany, a.CurrentJobTitle, a.CurrentCity, a.Skills,
                a.IsMentor, a.IsReferralProvider, a.VerificationStatus == "verified",
                a.GithubUrl, a.LinkedinUrl
            ))
            .ToListAsync();

        return Ok(new { total, page, pageSize, totalPages = (int)Math.Ceiling(total / (double)pageSize), items });
    }
}
```

---

## 5. Startup & JWT Bearer Configuration (`Program.cs`)

```csharp
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using System.Text;

var builder = WebApplication.CreateBuilder(args);

// DbContext
builder.Services.AddDbContext<CmsAlumniDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

// Authentication & JWT
var secret = builder.Configuration["Jwt:SecretKey"] ?? "cms-kanpur-bca-mca-super-secret-jwt-key-2025-secure-hash";
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secret)),
            ValidateIssuer = false,
            ValidateAudience = false,
            ClockSkew = TimeSpan.Zero
        };
    });

builder.Services.AddAuthorization();
builder.Services.AddControllers();

var app = builder.Build();

app.UseCors(policy => policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader());
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();
app.Run();
```
