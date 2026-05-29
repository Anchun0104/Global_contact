import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from database import engine, Base, SessionLocal
from auth import init_admin_user
import uvicorn

load_dotenv()

app = FastAPI(title="外联教授数据库管理系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def run_migrations():
    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("sqlite"):
        inspector = inspect(engine)
        columns = [c["name"] for c in inspector.get_columns("users")]
        if "display_name" not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR(100)"))
                conn.execute(text("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1"))
                conn.commit()

from routers import (
    auth as auth_router,
    professors,
    conferences,
    subconferences,
    cooperations,
    directions,
    stats,
    import_export,
    users,
    audit,
)

app.include_router(auth_router.router)
app.include_router(professors.router)
app.include_router(conferences.router)
app.include_router(subconferences.router)
app.include_router(cooperations.router)
app.include_router(directions.router)
app.include_router(stats.router)
app.include_router(import_export.router)
app.include_router(users.router)
app.include_router(audit.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


def init_demo_directions(db: Session):
    default_directions = [
        "法学", "计算机科学", "人工智能", "医学", "生物学",
        "物理学", "化学", "经济学", "管理学", "教育学",
        "心理学", "社会学", "数学", "工程学", "材料科学",
        "环境科学", "文学", "历史学", "哲学", "政治学",
        "艺术学", "新闻传播学", "建筑学", "农学", "药学",
    ]
    from models import ResearchDirection
    for name in default_directions:
        existing = db.query(ResearchDirection).filter(ResearchDirection.name == name).first()
        if not existing:
            db.add(ResearchDirection(name=name))
    db.commit()


@app.on_event("startup")
def startup():
    run_migrations()
    db = SessionLocal()
    try:
        init_admin_user(db)
        init_demo_directions(db)
    finally:
        db.close()


@app.get("/login")
def login_page():
    return FileResponse("templates/login.html")


@app.get("/")
def index():
    return FileResponse("templates/index.html")


@app.get("/pages/{page}")
def serve_page(page: str):
    if page == "dashboard":
        return RedirectResponse(url="/")
    path = os.path.join("templates", f"{page}.html")
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="页面不存在")


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=False)
