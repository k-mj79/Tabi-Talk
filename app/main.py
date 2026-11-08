import json, sqlite3, uuid, os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from . import rag

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db = sqlite3.connect(os.path.join(BASE, "chat.db"), check_same_thread=False)
db.row_factory = sqlite3.Row
db.executescript("""
CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, title TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, sid TEXT, role TEXT, content TEXT);
""")
app = FastAPI()

class Msg(BaseModel):
    message: str

@app.get("/api/sessions")
def sessions():
    return [dict(r) for r in db.execute("SELECT id,title FROM sessions ORDER BY rowid DESC")]

@app.post("/api/sessions")
def new_session():
    sid = uuid.uuid4().hex
    db.execute("INSERT INTO sessions(id,title) VALUES(?,?)", (sid, "새 대화")); db.commit()
    return {"id": sid, "title": "새 대화"}

@app.get("/api/sessions/{sid}")
def messages(sid: str):
    return [{"role": r["role"], "content": json.loads(r["content"])}
            for r in db.execute("SELECT role,content FROM messages WHERE sid=? ORDER BY id", (sid,))]

@app.delete("/api/sessions/{sid}")
def delete(sid: str):
    db.execute("DELETE FROM messages WHERE sid=?", (sid,))
    db.execute("DELETE FROM sessions WHERE id=?", (sid,)); db.commit()
    return {"ok": True}

@app.post("/api/sessions/{sid}/chat")
async def chat(sid: str, body: Msg):
    q = body.message.strip()
    if not q or not db.execute("SELECT 1 FROM sessions WHERE id=?", (sid,)).fetchone():
        raise HTTPException(400, "invalid request")
    rows = db.execute("SELECT role,content FROM messages WHERE sid=? ORDER BY id DESC LIMIT 6", (sid,)).fetchall()[::-1]
    history = [("human", json.loads(r["content"])) if r["role"] == "user"
               else ("ai", json.loads(r["content"]).get("translation", {}).get("jp", "")) for r in rows]
    try:
        answer = await rag.ask(q, history)
    except Exception as e:
        raise HTTPException(500, f"답변 생성 실패: {e}")
    db.execute("INSERT INTO messages(sid,role,content) VALUES(?,?,?)", (sid, "user", json.dumps(q, ensure_ascii=False)))
    db.execute("INSERT INTO messages(sid,role,content) VALUES(?,?,?)", (sid, "assistant", json.dumps(answer, ensure_ascii=False)))
    if db.execute("SELECT COUNT(*) FROM messages WHERE sid=?", (sid,)).fetchone()[0] == 2:
        db.execute("UPDATE sessions SET title=? WHERE id=?", (q[:30], sid))
    db.commit()
    return answer

app.mount("/", StaticFiles(directory=os.path.join(BASE, "static"), html=True))
