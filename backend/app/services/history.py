"""Thread-safe async run history service backed by Turso (libsql)."""

from datetime import datetime
from typing import List, Optional

from app.db import get_db
from app.logger import log


async def create_run(run_id: str, url: str) -> dict:
    conn = await get_db()
    started_at = datetime.utcnow().isoformat()
    
    conn.execute(
        "INSERT INTO runs (id, url, status, final_status, started_at, completed_at, error) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (run_id, url, "queued", None, started_at, None, None)
    )
    conn.commit()
    
    run = {
        "id": run_id,
        "url": url,
        "status": "queued",
        "final_status": None,
        "started_at": started_at,
        "completed_at": None,
        "error": None,
        "iterations": [],
    }
    log.info("history.run_created", run_id=run_id, url=url)
    return run


async def update_run(run_id: str, **kwargs) -> None:
    if not kwargs:
        return
    
    conn = await get_db()
    set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values())
    values.append(run_id)
    
    conn.execute(f"UPDATE runs SET {set_clause} WHERE id = ?", tuple(values))
    conn.commit()
    
    log.info("history.run_updated", run_id=run_id, **kwargs)


async def add_iteration(run_id: str, data: dict) -> None:
    conn = await get_db()
    
    conn.execute(
        "INSERT INTO iterations (run_id, step, url, answer, correct, next_url, explanation, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            run_id,
            data.get("step"),
            data.get("url"),
            data.get("answer"),
            data.get("correct"),
            data.get("next_url"),
            data.get("explanation"),
            data.get("timestamp")
        )
    )
    conn.commit()
    
    log.info("history.iteration_recorded", run_id=run_id, step=data.get("step"))


async def get_all() -> List[dict]:
    conn = await get_db()
    
    runs_cursor = conn.execute("SELECT * FROM runs ORDER BY started_at DESC")
    runs_rows = runs_cursor.fetchall()
    
    runs_map = {}
    runs_list = []
    
    for row in runs_rows:
        run_dict = {
            "id": row[0],
            "url": row[1],
            "status": row[2],
            "final_status": row[3],
            "started_at": row[4],
            "completed_at": row[5],
            "error": row[6],
            "iterations": []
        }
        runs_map[run_dict["id"]] = run_dict
        runs_list.append(run_dict)
        
    if not runs_list:
        return []
        
    iters_cursor = conn.execute("SELECT * FROM iterations ORDER BY id ASC")
    for row in iters_cursor.fetchall():
        run_id = row[1]
        if run_id in runs_map:
            iter_dict = {
                "step": row[2],
                "url": row[3],
                "answer": row[4],
                "correct": bool(row[5]),
                "next_url": row[6],
                "explanation": row[7],
                "timestamp": row[8]
            }
            runs_map[run_id]["iterations"].append(iter_dict)
            
    return runs_list


async def get_run(run_id: str) -> Optional[dict]:
    conn = await get_db()
    
    cursor = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
    row = cursor.fetchone()
    
    if not row:
        return None
        
    run_dict = {
        "id": row[0],
        "url": row[1],
        "status": row[2],
        "final_status": row[3],
        "started_at": row[4],
        "completed_at": row[5],
        "error": row[6],
        "iterations": []
    }
    
    iters_cursor = conn.execute("SELECT * FROM iterations WHERE run_id = ? ORDER BY id ASC", (run_id,))
    for iter_row in iters_cursor.fetchall():
        iter_dict = {
            "step": iter_row[2],
            "url": iter_row[3],
            "answer": iter_row[4],
            "correct": bool(iter_row[5]),
            "next_url": iter_row[6],
            "explanation": iter_row[7],
            "timestamp": iter_row[8]
        }
        run_dict["iterations"].append(iter_dict)
        
    return run_dict
