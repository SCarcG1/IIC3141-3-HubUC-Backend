from app.auth.auth_handler import create_access_token


def get_auth_header_for_tests(email: str, role: str, user_id: int) -> dict[str, str]:
    token = create_access_token({"sub": email, "role": role, "id": user_id})
    return {"Authorization": f"Bearer {token}"}
