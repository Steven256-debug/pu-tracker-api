from fastapi import APIRouter, HTTPException

from ..auth import verify_login, issue_token
from ..config import ROLES
from ..schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    if not verify_login(req.role, req.password):
        raise HTTPException(status_code=401, detail="Incorrect role or password.")
    cfg = ROLES[req.role]
    token = issue_token(req.role)
    return LoginResponse(
        token=token, role=req.role, faculty=cfg["faculty"],
        icon=cfg["icon"], tabs=cfg["tabs"],
    )


@router.get("/roles")
def list_roles():
    """Public — used to populate the role dropdown on the login screen."""
    return [{"role": name, "icon": cfg["icon"]} for name, cfg in ROLES.items()]
