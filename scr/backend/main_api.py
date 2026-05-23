import os
import psutil
import httpx
import uuid
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func, desc
from datetime import datetime
from typing import List
from database import init_db, async_session, ScanSession, Deal, Setting
from scanner_engine import scanner_instance, LOGS_DIR

app = FastAPI(title="Arbitrage Scanner AI PRO")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """Выполняется при запуске сервера: инициализирует базу данных"""
    await init_db()
@app.get("/api/system/stats")
async def get_system_stats():
    """
    Возвращает текущую нагрузку на сервер: CPU, RAM, Диск и кол-во ядер.
    Используется для отрисовки графиков в панельке.
    """
    return {
        "cpu": psutil.cpu_percent(interval=0.1),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('C:').percent,
        "cores": psutil.cpu_count(),
        "time": datetime.now().strftime("%H:%M:%S")
    }
@app.get("/api/deepseek/balance")
async def get_deepseek_balance_api():
    """
    Запрашивает актуальный баланс API ключа DeepSeek.
    Ключ берется из таблицы настроек в базе данных.
    """
    async with async_session() as session:
        key_res = await session.get(Setting, "DEEPSEEK_KEY")
        api_key = key_res.value if key_res else None
        
    if not api_key:
        return {"error": "API Key не найден в базе данных. Проверьте настройки."}

    url = "https://api.deepseek.com/user/balance"
    headers = {
        "Authorization": f"Bearer {api_key}", 
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'balance_infos' in data and len(data['balance_infos']) > 0:
                    b = data['balance_infos'][0]
                    return {
                        "is_available": data.get('is_available', False),
                        "total": f"{float(b.get('total_balance', 0)):.2f} {b.get('currency', 'USD')}",
                        "granted": b.get('granted_balance'),
                        "topped_up": b.get('topped_up_balance')
                    }
            return {
                "error": f"HTTP {resp.status_code}", 
                "message": resp.text
            }
        except Exception as e:
            return {"error": str(e)}
@app.get("/api/settings")
async def get_all_settings():
    """Возвращает все текущие настройки сканера из БД"""
    async with async_session() as session:
        res = await session.execute(select(Setting))
        return {s.key: s.value for s in res.scalars()}

@app.post("/api/settings")
async def update_settings(settings: dict):
    """
    Обновляет настройки в БД. 
    Принимает словарь, где ключ — название настройки, значение — новое значение.
    """
    async with async_session() as session:
        for k, v in settings.items():
            item = await session.get(Setting, k)
            if item:
                item.value = str(v)
            else:
                session.add(Setting(key=k, value=str(v)))
        await session.commit()
    return {"status": "success", "message": "Settings updated successfully"}
@app.post("/api/scan/start")
async def start_scan(background_tasks: BackgroundTasks):
    """
    Запускает новый процесс сканирования в фоновом режиме.
    Создает запись в таблице ScanSession и возвращает scan_id.
    """
    scan_id = str(uuid.uuid4())[:8]
    async with async_session() as session:
        new_session = ScanSession(id=scan_id, status="running")
        session.add(new_session)
        await session.commit()
    background_tasks.add_task(scanner_instance.run_scan, scan_id)
    return {"scan_id": scan_id, "status": "started"}

@app.get("/api/scan/status/{scan_id}")
async def get_scan_status(scan_id: str):
    """Возвращает текущий прогресс и статус конкретной сессии сканирования"""
    async with async_session() as session:
        scan = await session.get(ScanSession, scan_id)
        if not scan:
            raise HTTPException(status_code=404, detail="Session not found")
        return scan

@app.get("/api/scan/results/{scan_id}")
async def get_scan_results(scan_id: str):
    """Возвращает все найденные арбитражные сделки для указанного scan_id"""
    async with async_session() as session:
        stmt = select(Deal).where(Deal.scan_id == scan_id)
        res = await session.execute(stmt)
        return [d.data for d in res.scalars().all()]

@app.post("/api/reparse")
async def reparse_deals(deals: List[dict]):
    try:
        updated = await scanner_instance.reparse_active_deals(deals)
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scan/log/{scan_id}")
async def get_scan_log(scan_id: str):
    """
    Позволяет скачать или просмотреть файл лога для конкретной сессии.
    Используется для вывода 'консоли' на фронтенде.
    """
    file_path = os.path.join(LOGS_DIR, f"scan_{scan_id}.log")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='text/plain', filename=f"scan_{scan_id}.log")
    raise HTTPException(status_code=404, detail="Log file not found")
@app.get("/api/stats/global")
async def get_global_stats():
    """Возвращает общую статистику: сколько всего сделок в БД и сколько было сканирований"""
    async with async_session() as session:
        deals_count = await session.execute(select(func.count(Deal.id)))
        scans_count = await session.execute(select(func.count(ScanSession.id)))
        return {
            "total_deals_in_db": deals_count.scalar(),
            "total_scans_performed": scans_count.scalar(),
            "server_time": datetime.now().isoformat()
        }
@app.get("/api/scan/latest")
async def get_latest_scan():
    """Возвращает результаты самого последнего успешного сканирования (для автозагрузки на главной)"""
    async with async_session() as session:
        stmt = select(ScanSession).where(ScanSession.status == "completed").order_by(desc(ScanSession.id)).limit(1)
        res = await session.execute(stmt)
        latest_scan = res.scalar_one_or_none()
        
        if not latest_scan:
            return {"scan_id": None, "deals": []}
        deals_stmt = select(Deal).where(Deal.scan_id == latest_scan.id)
        deals_res = await session.execute(deals_stmt)
        deals = [d.data for d in deals_res.scalars().all()]
        
        return {
            "scan_id": latest_scan.id,
            "end_time": latest_scan.end_time.isoformat() if latest_scan.end_time else None,
            "deals": deals
        }

@app.get("/api/history")
async def get_scan_history():
    """Возвращает список всех завершенных сканирований для вкладки 'История'"""
    async with async_session() as session:
        stmt = select(ScanSession).where(ScanSession.status == "completed").order_by(desc(ScanSession.id))
        res = await session.execute(stmt)
        history = []
        for scan in res.scalars().all():
            history.append({
                "id": scan.id,
                "total_deals": scan.total_deals,
                "end_time": scan.end_time.isoformat() if scan.end_time else "Неизвестно"
            })
        return history

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)