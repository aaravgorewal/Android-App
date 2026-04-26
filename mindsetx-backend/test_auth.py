"""
test_auth.py — Manual test script for the MindsetX auth flow.

Tests the complete auth lifecycle without needing a browser or Postman:
  signup → login → get profile → refresh token → change password → delete account

Run with a live server:
  # Terminal 1:
  python run.py

  # Terminal 2:
  python test_auth.py
"""

import asyncio
import sys
import httpx

BASE_URL = "http://localhost:8000"

TEST_EMAIL = "testuser@mindsetx.dev"
TEST_PASSWORD = "SecurePass1"
NEW_PASSWORD = "NewSecurePass2"


async def run():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        print("=" * 60)
        print("MindsetX Auth Flow Test")
        print("=" * 60)

        # ── 1. Signup ─────────────────────────────────────────────────
        print("\n1. POST /auth/signup")
        r = await client.post("/auth/signup", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Test User"
        })
        if r.status_code == 409:
            print("  ⚠️  User already exists — skipping signup, continuing with login.")
        elif r.status_code == 201:
            data = r.json()
            assert "access_token" in data, "No access_token in signup response"
            assert "refresh_token" in data, "No refresh_token in signup response"
            print(f"  ✅ Signup OK — access_token: {data['access_token'][:30]}...")
        else:
            print(f"  ❌ FAIL {r.status_code}: {r.text}")
            sys.exit(1)

        # ── 2. Login ──────────────────────────────────────────────────
        print("\n2. POST /auth/login")
        r = await client.post("/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        })
        assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
        tokens = r.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        print(f"  ✅ Login OK — expires_in: {tokens['expires_in']}s")

        headers = {"Authorization": f"Bearer {access_token}"}

        # ── 3. Rejected password (wrong) ──────────────────────────────
        print("\n3. POST /auth/login (wrong password)")
        r = await client.post("/auth/login", json={
            "email": TEST_EMAIL,
            "password": "WrongPass999",
        })
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("  ✅ Wrong password correctly rejected (401)")

        # ── 4. GET /auth/me ───────────────────────────────────────────
        print("\n4. GET /auth/me")
        r = await client.get("/auth/me", headers=headers)
        assert r.status_code == 200, f"GET /me failed: {r.status_code}"
        me = r.json()
        assert me["email"] == TEST_EMAIL
        print(f"  ✅ Profile returned — email: {me['email']}, name: {me['full_name']}")

        # ── 5. PATCH /auth/me ─────────────────────────────────────────
        print("\n5. PATCH /auth/me")
        r = await client.patch("/auth/me", headers=headers, json={"full_name": "Updated Name"})
        assert r.status_code == 200
        assert r.json()["full_name"] == "Updated Name"
        print("  ✅ Name updated successfully")

        # ── 6. Refresh token ──────────────────────────────────────────
        print("\n6. POST /auth/refresh")
        r = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert r.status_code == 200, f"Refresh failed: {r.status_code} {r.text}"
        new_access = r.json()["access_token"]
        assert new_access != access_token, "Refresh returned same token"
        print(f"  ✅ New access token issued — {new_access[:30]}...")

        # ── 7. Invalid refresh token ──────────────────────────────────
        print("\n7. POST /auth/refresh (invalid token)")
        r = await client.post("/auth/refresh", json={"refresh_token": "this.is.fake"})
        assert r.status_code == 401
        print("  ✅ Invalid refresh token correctly rejected (401)")

        # ── 8. Change password ────────────────────────────────────────
        print("\n8. POST /auth/change-password")
        r = await client.post("/auth/change-password", headers=headers, json={
            "current_password": TEST_PASSWORD,
            "new_password": NEW_PASSWORD,
        })
        assert r.status_code == 204, f"Change password failed: {r.status_code} {r.text}"
        print("  ✅ Password changed successfully")

        # Login with new password to confirm
        r = await client.post("/auth/login", json={"email": TEST_EMAIL, "password": NEW_PASSWORD})
        assert r.status_code == 200
        headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        print("  ✅ Login with new password confirmed")

        # ── 9. Logout ─────────────────────────────────────────────────
        print("\n9. POST /auth/logout")
        r = await client.post("/auth/logout", headers=headers)
        assert r.status_code == 204
        print("  ✅ Logout successful (204 No Content)")

        # ── 10. Delete account ────────────────────────────────────────
        print("\n10. DELETE /auth/me")
        r = await client.delete("/auth/me", headers=headers)
        assert r.status_code == 204
        print("  ✅ Account deleted")

        # Confirm 401 after deletion
        r = await client.get("/auth/me", headers=headers)
        assert r.status_code == 401
        print("  ✅ Deleted account correctly returns 401")

        print("\n" + "=" * 60)
        print("ALL AUTH TESTS PASSED ✅")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run())
