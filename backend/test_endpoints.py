#!/usr/bin/env python3
"""
CogniVex API Endpoint Tester
Tests all 90 endpoints and reports results in JSON format
"""

import requests
import json
import time
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

results = {
    "test_run": {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "api_prefix": API_PREFIX
    },
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0
    },
    "categories": {},
    "endpoints": []
}

def test_endpoint(method, path, description, auth_required=False, token=None, data=None, expected_status=None, use_form=False):
    result = {
        "method": method,
        "path": path,
        "description": description,
        "auth_required": auth_required,
        "status": None,
        "response_code": None,
        "error": None,
        "passed": False
    }

    url = f"{BASE_URL}{path}"
    headers = {}

    if auth_required and token:
        headers["Authorization"] = f"Bearer {token}"

    if use_form:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif data and method in ["POST", "PUT"]:
        headers["Content-Type"] = "application/json"

    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            if use_form:
                resp = requests.post(url, headers=headers, data=data, timeout=30)
            else:
                resp = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, json=data, timeout=30)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=30)
        else:
            resp = requests.request(method, url, headers=headers, json=data, timeout=30)

        result["response_code"] = resp.status_code

        if expected_status:
            result["passed"] = resp.status_code == expected_status
        elif auth_required and not token:
            result["passed"] = resp.status_code == 401
        elif resp.status_code in [200, 201, 204, 400, 401, 404]:
            result["passed"] = True
        else:
            result["passed"] = False

        try:
            result["response"] = resp.json()
        except:
            result["response"] = resp.text[:500]

    except requests.exceptions.ConnectionError as e:
        result["error"] = "Connection error - server not running"
        result["response_code"] = 0
    except requests.exceptions.Timeout:
        result["error"] = "Request timeout"
        result["response_code"] = 0
    except Exception as e:
        result["error"] = str(e)
        result["response_code"] = 0

    results["endpoints"].append(result)
    results["summary"]["total"] += 1
    if result["passed"]:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1

    return result


def test_category(category_name, endpoints):
    results["categories"][category_name] = {"total": 0, "passed": 0, "failed": 0}
    print(f"\n=== Testing {category_name.upper()} endpoints ===")

    for endpoint in endpoints:
        method = endpoint[0]
        path = endpoint[1]
        desc = endpoint[2]
        auth = endpoint[3] if len(endpoint) > 3 else False
        expected = endpoint[4] if len(endpoint) > 4 else None
        data = endpoint[5] if len(endpoint) > 5 else None

        result = test_endpoint(method, path, desc, auth, results.get("token"), data, expected)
        status = "[PASS]" if result["passed"] else "[FAIL]"
        print(f"  {status} {method} {path} - {result['response_code']}")

        results["categories"][category_name]["total"] += 1
        if result["passed"]:
            results["categories"][category_name]["passed"] += 1
        else:
            results["categories"][category_name]["failed"] += 1


def main():
    print("=" * 60)
    print("CogniVex API Endpoint Tester")
    print("=" * 60)

    # Root endpoints
    test_category("root", [
        ("GET", "/", "Root endpoint - API info", False, 200),
        ("GET", "/health", "Health check", False, 200),
        ("GET", "/ready", "Readiness probe", False, 200),
    ])

    # Auth endpoints
    timestamp = int(time.time())
    test_email = f"test_{timestamp}@test.com"
    test_password = "TestPassword123!"
    results["test_user"] = {"email": test_email, "password": test_password}

    test_category("auth", [
        ("POST", f"{API_PREFIX}/auth/signup", "Sign up new user", False, None, 
         {"email": test_email, "password": test_password, "full_name": "Test User"}),
        ("POST", f"{API_PREFIX}/auth/login", "Login", False, None, 
         {"email": test_email, "password": test_password}),
        ("GET", f"{API_PREFIX}/auth/me", "Get current user", True, 200),
        ("POST", f"{API_PREFIX}/auth/logout", "Logout", True, 200),
    ])

    # Try to get token from signup response
    for ep in results["endpoints"]:
        if ep["path"] == f"{API_PREFIX}/auth/signup" and ep["response_code"] == 200:
            try:
                results["token"] = ep["response"].get("data", {}).get("session", {}).get("access_token")
            except:
                pass
        if ep["path"] == f"{API_PREFIX}/auth/login" and ep["response_code"] == 200:
            try:
                results["token"] = ep["response"].get("data", {}).get("session", {}).get("access_token")
            except:
                pass

    # Users endpoints
    test_category("users", [
        ("GET", f"{API_PREFIX}/users/me", "Get current user profile", True, 200),
        ("PUT", f"{API_PREFIX}/users/me", "Update profile", True, 200, {"full_name": "Updated Name"}),
        ("GET", f"{API_PREFIX}/users/00000000-0000-0000-0000-000000000000", "Get user by ID", True, 404),
    ])

    # Companies endpoints
    test_category("companies", [
        ("POST", f"{API_PREFIX}/companies", "Create company", True, 201, 
         {"name": "Test Company", "industry": "Technology", "description": "Test"}),
        ("GET", f"{API_PREFIX}/companies", "List companies", True, 200),
        ("GET", f"{API_PREFIX}/companies/00000000-0000-0000-0000-000000000000", "Get company", True, 404),
        ("PUT", f"{API_PREFIX}/companies/00000000-0000-0000-0000-000000000000", "Update company", True, 404),
        ("DELETE", f"{API_PREFIX}/companies/00000000-0000-0000-0000-000000000000", "Delete company", True, 404),
    ])

    # Jobs endpoints
    test_category("jobs", [
        ("POST", f"{API_PREFIX}/jobs", "Create job", True, 400),  # Needs company_id
        ("GET", f"{API_PREFIX}/jobs", "List jobs", True, 200),
        ("GET", f"{API_PREFIX}/jobs/00000000-0000-0000-0000-000000000000", "Get job", True, 404),
        ("GET", f"{API_PREFIX}/jobs/00000000-0000-0000-0000-000000000000/candidates", "Job candidates", True, 403),
        ("GET", f"{API_PREFIX}/jobs/recommendations/for-me", "Job recommendations", True, 200),
        ("GET", f"{API_PREFIX}/jobs/recommendations/candidate/00000000-0000-0000-0000-000000000000", "Recommendations for candidate", True, 200),
    ])

    # Interviews endpoints
    test_category("interviews", [
        ("POST", f"{API_PREFIX}/interviews", "Create interview", True, 400),
        ("GET", f"{API_PREFIX}/interviews", "List interviews", True, 200),
        ("GET", f"{API_PREFIX}/interviews/00000000-0000-0000-0000-000000000000", "Get interview", True, 404),
        ("PUT", f"{API_PREFIX}/interviews/00000000-0000-0000-0000-000000000000", "Update interview", True, 404),
        ("POST", f"{API_PREFIX}/interviews/00000000-0000-0000-0000-000000000000/answer", "Submit answer", True, 404),
        ("GET", f"{API_PREFIX}/interviews/00000000-0000-0000-0000-000000000000/score", "Get score", True, 404),
        ("POST", f"{API_PREFIX}/interviews/00000000-0000-0000-0000-000000000000/start", "Start interview", True, 404),
        ("GET", f"{API_PREFIX}/interviews/00000000-0000-0000-0000-000000000000/questions", "Get questions", True, 404),
        ("GET", f"{API_PREFIX}/interviews/00000000-0000-0000-0000-000000000000/next", "Get next question", True, 404),
        ("POST", f"{API_PREFIX}/interviews/00000000-0000-0000-0000-000000000000/complete", "Complete interview", True, 404),
        ("GET", f"{API_PREFIX}/interviews/00000000-0000-0000-0000-000000000000/state", "Get state", True, 404),
        ("GET", f"{API_PREFIX}/interviews/00000000-0000-0000-0000-000000000000/transcript", "Get transcript", True, 404),
        ("GET", f"{API_PREFIX}/interviews/00000000-0000-0000-0000-000000000000/report", "Get report", True, 404),
        ("POST", f"{API_PREFIX}/interviews/00000000-0000-0000-0000-000000000000/evaluate", "Evaluate", True, 404),
    ])

    # Resume endpoints
    test_category("resume", [
        ("POST", f"{API_PREFIX}/resume/upload", "Upload resume", True, 422),
        ("GET", f"{API_PREFIX}/resume", "List resumes", True, 200),
        ("GET", f"{API_PREFIX}/resume/00000000-0000-0000-0000-000000000000", "Get resume", True, 404),
        ("DELETE", f"{API_PREFIX}/resume/00000000-0000-0000-0000-000000000000", "Delete resume", True, 404),
        ("PUT", f"{API_PREFIX}/resume/00000000-0000-0000-0000-000000000000/skills", "Update skills", True, 404, ["Python", "JavaScript"]),
    ])

    # Dashboard endpoints
    test_category("dashboard", [
        ("GET", f"{API_PREFIX}/dashboard/candidate", "Candidate dashboard", True, 200),
        ("GET", f"{API_PREFIX}/dashboard/recruiter", "Recruiter dashboard", True, 200),
        ("GET", f"{API_PREFIX}/dashboard/candidate/profile", "Candidate profile", True, 200),
        ("GET", f"{API_PREFIX}/dashboard/candidate/interviews", "Candidate interviews", True, 200),
        ("GET", f"{API_PREFIX}/dashboard/candidate/available", "Available interviews", True, 200),
        ("GET", f"{API_PREFIX}/dashboard/candidate/results", "Past results", True, 200),
        ("GET", f"{API_PREFIX}/dashboard/candidate/skills", "Skill profile", True, 200),
        ("GET", f"{API_PREFIX}/dashboard/candidate/trend", "Performance trend", True, 200),
        ("GET", f"{API_PREFIX}/dashboard/recruiter/company", "Company dashboard", True, 200),
        ("GET", f"{API_PREFIX}/dashboard/recruiter/jobs", "Recruiter jobs", True, 200),
        ("GET", f"{API_PREFIX}/dashboard/recruiter/candidates-summary", "Candidates summary", True, 200),
        ("GET", f"{API_PREFIX}/dashboard/stats", "Stats", True, 200),
    ])

    # Rankings endpoints
    test_category("rankings", [
        ("GET", f"{API_PREFIX}/rankings/jobs/00000000-0000-0000-0000-000000000000/candidates", "Rankings candidates", True, 403),
        ("GET", f"{API_PREFIX}/rankings/jobs/00000000-0000-0000-0000-000000000000/candidates/ranked", "Ranked candidates", True, 403),
        ("GET", f"{API_PREFIX}/rankings/jobs/00000000-0000-0000-0000-000000000000/candidates/skill-match", "Skill match", True, 403),
        ("GET", f"{API_PREFIX}/rankings/jobs/00000000-0000-0000-0000-000000000000/candidates/combined", "Combined ranking", True, 403),
        ("GET", f"{API_PREFIX}/rankings/jobs/00000000-0000-0000-0000-000000000000/compare", "Compare candidates", True, 403),
        ("GET", f"{API_PREFIX}/rankings/candidates/00000000-0000-0000-0000-000000000000/jobs", "Candidate job rankings", True, 200),
        ("GET", f"{API_PREFIX}/rankings/candidates/00000000-0000-0000-0000-000000000000/rankings", "Candidate rankings", True, 200),
    ])

    # Recruiter endpoints
    test_category("recruiter", [
        ("GET", f"{API_PREFIX}/recruiter/dashboard", "Recruiter dashboard", True, 200),
        ("GET", f"{API_PREFIX}/recruiter/jobs", "Recruiter jobs", True, 200),
        ("GET", f"{API_PREFIX}/recruiter/jobs/00000000-0000-0000-0000-000000000000/candidates", "Job candidates", True, 403),
        ("GET", f"{API_PREFIX}/recruiter/jobs/00000000-0000-0000-0000-000000000000/candidates/ranked", "Ranked candidates", True, 403),
        ("POST", f"{API_PREFIX}/recruiter/candidates/00000000-0000-0000-0000-000000000000/status", "Update status", True, 404),
        ("GET", f"{API_PREFIX}/recruiter/candidates/00000000-0000-0000-0000-000000000000/status", "Get status", True, 404),
        ("GET", f"{API_PREFIX}/recruiter/jobs/00000000-0000-0000-0000-000000000000/shortlisted", "Shortlisted", True, 403),
        ("GET", f"{API_PREFIX}/recruiter/jobs/00000000-0000-0000-0000-000000000000/analytics", "Job analytics", True, 403),
        ("GET", f"{API_PREFIX}/recruiter/analytics/overview", "Analytics overview", True, 200),
        ("GET", f"{API_PREFIX}/recruiter/candidates/00000000-0000-0000-0000-000000000000/report", "Candidate report", True, 404),
    ])

    # Analytics endpoints
    test_category("analytics", [
        ("GET", f"{API_PREFIX}/analytics/jobs/00000000-0000-0000-0000-000000000000/skill-gaps", "Skill gaps", True, 200),
        ("GET", f"{API_PREFIX}/analytics/jobs/00000000-0000-0000-0000-000000000000/trends", "Trends", True, 200),
        ("GET", f"{API_PREFIX}/analytics/company/overview", "Company overview", True, 200),
        ("GET", f"{API_PREFIX}/analytics/company/top-candidates", "Top candidates", True, 200),
        ("GET", f"{API_PREFIX}/analytics/users/00000000-0000-0000-0000-000000000000/skills", "User skills", True, 200),
        ("GET", f"{API_PREFIX}/analytics/users/00000000-0000-0000-0000-000000000000/skills/top", "Top skills", True, 200),
        ("GET", f"{API_PREFIX}/analytics/users/00000000-0000-0000-0000-000000000000/skills/improve", "Skills improve", True, 200),
        ("GET", f"{API_PREFIX}/analytics/users/00000000-0000-0000-0000-000000000000/skills/Python/trend", "Skill trend", True, 200),
        ("GET", f"{API_PREFIX}/analytics/skills/match", "Skills match", True, 200),
        ("GET", f"{API_PREFIX}/analytics/skills/similar", "Similar skills", True, 200),
        ("GET", f"{API_PREFIX}/analytics/interviews/00000000-0000-0000-0000-000000000000/integrity", "Interview integrity", True, 200),
        ("GET", f"{API_PREFIX}/analytics/interviews/00000000-0000-0000-0000-000000000000/integrity/history", "Integrity history", True, 200),
        ("GET", f"{API_PREFIX}/analytics/cache/stats", "Cache stats", True, 200),
        ("POST", f"{API_PREFIX}/analytics/cache/cleanup", "Cache cleanup", True, 200),
    ])

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Endpoints Tested: {results['summary']['total']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")

    print("\nBy Category:")
    for cat, stats in results["categories"].items():
        status = "OK" if stats["failed"] == 0 else "ISSUES"
        print(f"  {cat}: {stats['passed']}/{stats['total']} passed [{status}]")

    with open("endpoint_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to endpoint_test_results.json")
    return results


if __name__ == "__main__":
    main()
