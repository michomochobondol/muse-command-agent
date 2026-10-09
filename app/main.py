"""Backend FastAPI - "ruang kontrol" Web Command Center."""

import asyncio
import datetime
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from app.crew import build_crew

load_dotenv()

app = FastAPI(title="Web Command Center API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MVP: in-memory store. Produksi: ganti Redis + Postgres.
jobs: dict = {}


class CommandIn(BaseModel):
    objective: str


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def add_log(job_id: str, msg: str):
    if job_id in jobs:
        jobs[job_id]["logs"].append(f"[{_now()}] {msg}")


async def run_crew(job_id: str):
    jobs[job_id]["status"] = "running"
    add_log(job_id, "Crew mulai bekerja")
    try:
        crew = build_crew(jobs[job_id]["objective"])
        add_log(job_id, "Researcher mengumpulkan data...")
        result = await asyncio.to_thread(crew.kickoff)
        jobs[job_id]["result"] = str(result)
        jobs[job_id]["status"] = "done"
        add_log(job_id, "Crew selesai")
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["result"] = f"Error: {e}"
        add_log(job_id, f"Error: {e}")


@app.post("/api/jobs")
async def create_job(cmd: CommandIn, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "job_id": job_id,
        "objective": cmd.objective,
        "status": "queued",
        "result": None,
        "logs": [f"[{_now()}] Job dibuat: {cmd.objective}"],
        "created_at": _now(),
    }
    background_tasks.add_task(run_crew, job_id)
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    if job_id not in jobs:
        return {"error": "job tidak ditemukan"}
    return jobs[job_id]


@app.websocket("/ws/jobs/{job_id}")
async def ws_logs(websocket: WebSocket, job_id: str):
    await websocket.accept()
    try:
        sent = 0
        while True:
            if job_id not in jobs:
                await websocket.send_json({"error": "job tidak ditemukan"})
                break
            logs = jobs[job_id]["logs"]
            while sent < len(logs):
                await websocket.send_json(
                    {"log": logs[sent], "status": jobs[job_id]["status"]}
                )
                sent += 1
            if jobs[job_id]["status"] in ("done", "error"):
                await websocket.send_json(
                    {
                        "status": jobs[job_id]["status"],
                        "result": jobs[job_id]["result"],
                        "done": True,
                    }
                )
                break
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@app.get("/")
async def root():
    return {"ok": True, "service": "web-command-center"}


@app.get("/debug")
async def debug():
    """Endpoint diagnostik sementara: cek versi crewai dan status patch."""
    import crewai
    import crewai.llms.cache as cache_mod
    from crewai.llm import LLM

    test_msg = {"role": "system", "content": "x"}
    marked = cache_mod.mark_cache_breakpoint(test_msg)

    return {
        "crewai_version": getattr(crewai, "__version__", "unknown"),
        "mark_cache_breakpoint_is_noop": "cache_breakpoint" not in marked,
        "format_method_patched": "CACHE_BREAKPOINT_KEY"
        in getattr(LLM._format_messages_for_provider, "__code__", {}).co_names
        if hasattr(LLM._format_messages_for_provider, "__code__")
        else "unknown",
    }
