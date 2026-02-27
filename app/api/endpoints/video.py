from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from app.api.dependencies import get_db
from app.schemas.video_schema import ParseRequest, ParseResponse, DownloadRequest, DownloadResponse, TaskResponse
from app.services.downloader import parse_video
from app.models.base import Task, TaskStatus
from app.services.task_manager import process_download_task
from app.core.config import settings

router = APIRouter()


@router.post("/parse", response_model=ParseResponse)
def parse_video_url(req: ParseRequest, db: Session = Depends(get_db)):
    try:
        return parse_video(req.url, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/download")
async def download_video_url(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        body = await request.json()
        req = DownloadRequest(**body)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    fid = req.format_id if req.format_id else "best"

    new_task = Task(
        id=str(uuid.uuid4()),
        url=req.url,
        format_id=fid,
        status=TaskStatus.PENDING
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    background_tasks.add_task(process_download_task, new_task.id, db)

    return DownloadResponse(task_id=new_task.id, status=new_task.status)


@router.get("/tasks", response_model=List[TaskResponse])
def get_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.created_at.desc()).limit(50).all()
    return [
        {
            "id": t.id,
            "url": t.url,
            "title": t.title,
            "status": t.status,
            "format_id": t.format_id,
            "error_msg": t.error_msg,
            "created_at": t.created_at.isoformat() if t.created_at else "",
            "local_url": f"/downloads/{os.path.relpath(t.local_path, settings.TEMP_DOWNLOAD_DIR)}" if t.local_path else None,
        }
        for t in tasks
    ]

@router.get("/cookies/status")
def get_cookie_status():
    status = {
        "bilibili": False,
        "douyin": False,
        "youtube": False
    }
    
    cookie_path = settings.COOKIES_FILE
    if os.path.exists(cookie_path):
        try:
            with open(cookie_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Check for domain presence in Netscape format
                if ".bilibili.com" in content:
                    status["bilibili"] = True
                if ".douyin.com" in content:
                    status["douyin"] = True
                if ".youtube.com" in content:
                    status["youtube"] = True
        except Exception:
            pass
            
    return status
