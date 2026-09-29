# PHP Laravel Compatibility Architecture Guide

## 1. Overview & Architectural Mapping

The CMS Kanpur Alumni Platform backend can be implemented directly using **PHP 8.2+ and Laravel 11**. By leveraging Laravel Eloquent, FormRequest validation, and API Resource Transformers, the platform maintains complete parity with the PostgreSQL database schema and client REST API specifications.

```
Python FastAPI Layer                    PHP Laravel Layer
--------------------                    -----------------
app/routers/auth.py            --->     app/Http/Controllers/Api/AuthController.php
app/routers/users.py           --->     app/Http/Controllers/Api/AlumniController.php
app/routers/jobs.py            --->     app/Http/Controllers/Api/JobController.php
app/routers/mentorship.py      --->     app/Http/Controllers/Api/MentorshipController.php
app/routers/admin.py           --->     app/Http/Controllers/Api/AdminController.php
app/models/*.py                --->     app/Models/*.php (Eloquent Models)
app/schemas/*.py               --->     app/Http/Requests/* & app/Http/Resources/*
app/core/dependencies.py       --->     app/Http/Middleware/EnsureUserRole.php
```

---

## 2. Directory Structure

```
app/
├── Http/
│   ├── Controllers/
│   │   └── Api/
│   │       ├── AuthController.php
│   │       ├── AlumniController.php
│   │       ├── JobController.php
│   │       ├── MentorshipController.php
│   │       ├── ProjectController.php
│   │       ├── ResourceController.php
│   │       ├── EventController.php
│   │       └── AdminController.php
│   ├── Middleware/
│   │   ├── EnsureUserRole.php
│   │   └── EnsureVerifiedAlumnus.php
│   ├── Requests/
│   │   ├── RegisterRequest.php
│   │   ├── JobCreateRequest.php
│   │   └── ReferralCreateRequest.php
│   └── Resources/
│       ├── AlumniResource.php
│       ├── JobResource.php
│       └── ReferralResource.php
├── Models/
│   ├── User.php
│   ├── AuthorizedCollegeRegistry.php
│   ├── StudentProfile.php
│   ├── AlumniProfile.php
│   ├── AlumniProject.php
│   ├── Job.php
│   ├── ReferralRequest.php
│   └── MentorshipProfile.php
database/
├── migrations/                        # Normalized migration tables matching schema
└── seeders/
    └── CmsAlumniSeeder.php            # Equivalent seed dataset
routes/
└── api.php                            # Defined API route declarations
```

---

## 3. Eloquent Model (`AlumniProfile.php`)

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class AlumniProfile extends Model
{
    protected $table = 'alumni_profiles';

    protected $fillable = [
        'user_id',
        'full_name',
        'enrollment_no',
        'roll_no',
        'course',
        'batch_year',
        'graduation_year',
        'bio',
        'avatar_url',
        'current_company',
        'current_job_title',
        'industry',
        'years_of_experience',
        'current_city',
        'country',
        'skills',
        'github_url',
        'linkedin_url',
        'leetcode_url',
        'is_mentor',
        'is_referral_provider',
        'verification_status',
        'verification_notes',
    ];

    protected $casts = [
        'is_mentor' => 'boolean',
        'is_referral_provider' => 'boolean',
        'years_of_experience' => 'float',
    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function projects(): HasMany
    {
        return $this->hasMany(AlumniProject::class, 'alumni_id');
    }

    public function experiences(): HasMany
    {
        return $this->hasMany(AlumniExperience::class, 'alumni_id');
    }
}
```

---

## 4. API Routes (`routes/api.php`)

```php
<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\AlumniController;
use App\Http\Controllers\Api\JobController;
use App\Http\Controllers\Api\MentorshipController;
use App\Http\Controllers\Api\AdminController;

Route::prefix('auth')->group(function () {
    Route::post('/register', [AuthController::class, 'register']);
    Route::post('/login', [AuthController::class, 'login']);
    Route::post('/logout', [AuthController::class, 'logout'])->middleware('auth:sanctum');
    Route::get('/me', [AuthController::class, 'me'])->middleware('auth:sanctum');
});

Route::get('/alumni', [AlumniController::class, 'index']);
Route::get('/alumni/{id}', [AlumniController::class, 'show']);

Route::get('/jobs', [JobController::class, 'index']);
Route::get('/jobs/{id}', [JobController::class, 'show']);

Route::middleware('auth:sanctum')->group(function () {
    Route::post('/jobs', [JobController::class, 'store']);
    Route::post('/jobs/{id}/apply', [JobController::class, 'apply']);
    Route::post('/referrals/request', [JobController::class, 'requestReferral']);
    Route::get('/referrals/my-requests', [JobController::class, 'myReferrals']);
    Route::put('/referrals/{id}/status', [JobController::class, 'updateReferralStatus']);

    // Admin routes
    Route::middleware('role:admin,super_admin,faculty')->prefix('admin')->group(function () {
        Route::get('/dashboard', [AdminController::class, 'dashboard']);
        Route::get('/verifications', [AdminController::class, 'verifications']);
        Route::put('/verifications/{id}', [AdminController::class, 'updateVerification']);
    });
});
```

---

## 5. Controller Implementation (`AlumniController.php`)

```php
<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\AlumniProfile;
use App\Http\Resources\AlumniResource;
use Illuminate\Http\Request;

class AlumniController extends Controller
{
    public function index(Request $request)
    {
        $query = AlumniProfile::with('user')->whereHas('user', function ($q) {
            $q->where('is_active', true);
        });

        if ($request->filled('q')) {
            $term = '%' . $request->q . '%';
            $query->where(function ($q) use ($term) {
                $q->where('full_name', 'like', $term)
                  ->orWhere('current_company', 'like', $term)
                  ->orWhere('current_job_title', 'like', $term)
                  ->orWhere('skills', 'like', $term);
            });
        }

        if ($request->filled('course')) {
            $query->where('course', strtoupper($request->course));
        }

        if ($request->filled('technology')) {
            $query->where('skills', 'like', '%' . $request->technology . '%');
        }

        if ($request->boolean('mentorship')) {
            $query->where('is_mentor', true);
        }

        if ($request->boolean('referral')) {
            $query->where('is_referral_provider', true);
        }

        $perPage = min((int) $request->input('page_size', 12), 50);
        $alumni = $query->orderBy('batch_year', 'desc')->paginate($perPage);

        return response()->json([
            'total' => $alumni->total(),
            'page' => $alumni->currentPage(),
            'page_size' => $alumni->perPage(),
            'total_pages' => $alumni->lastPage(),
            'items' => AlumniResource::collection($alumni)
        ]);
    }
}
```
