import asyncio
import os
import json
import logging
import uuid
import sys
from datetime import datetime
from sqlalchemy import update, select

from database import async_session, ScanSession, Deal, Setting
from module_polymarket import get_polymarket_politics, get_single_polymarket_event
from module_kalshi import get_kalshi_politics, get_single_kalshi_event
from module_arbitrage import calculate_arbitrage, filter_by_profit
from module_matcher import HybridMatcher
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DEBUG_DIR = os.path.join(BASE_DIR, "debug")
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)

class ArbitrageScanner:
    def __init__(self):
        pass

    def setup_scan_logger(self, scan_id):
        """Индивидуальное логирование для каждой сессии"""
        logger = logging.getLogger(f"scan_{scan_id}")
        logger.setLevel(logging.DEBUG)
        log_file = os.path.join(LOGS_DIR, f"scan_{scan_id}.log")
        
        if logger.hasHandlers():
            logger.handlers.clear()
            
        fh = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        return logger

    async def get_settings(self):
        """Загрузка актуальных настроек из базы данных"""
        async with async_session() as session:
            res = await session.execute(select(Setting))
            return {row.key: row.value for row in res.scalars()}

    def save_debug_json(self, scan_id, filename, data):
        """Сохранение дампов данных в режиме Debug"""
        session_debug_dir = os.path.join(DEBUG_DIR, scan_id)
        os.makedirs(session_debug_dir, exist_ok=True)
        file_path = os.path.join(session_debug_dir, f"{filename}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    async def update_db_status(self, scan_id, **kwargs):
        """Обновление прогресса и статистики в БД"""
        async with async_session() as session:
            stmt = update(ScanSession).where(ScanSession.id == scan_id).values(**kwargs)
            await session.execute(stmt)
            await session.commit()

    async def reparse_active_deals(self, deals_list: list):
        if not deals_list: return []

        def normalize(text):
            return " ".join(text.lower().split()).strip().replace('?', '')

        poly_slugs = list(set([d['poly'].get('slug') for d in deals_list if d['poly'].get('slug')]))
        kalshi_tickers = list(set([d['kalshi'].get('series_ticker') for d in deals_list if d['kalshi'].get('series_ticker')]))
        
        settings = await self.get_settings()
        bankroll = float(settings.get("BANKROLL", 1000))
        min_p = float(settings.get("MIN_PRICE_THRESHOLD", 0.10))
        max_p = float(settings.get("MAX_PRICE_THRESHOLD", 0.90))

        poly_tasks = [get_single_polymarket_event(slug) for slug in poly_slugs]
        kalshi_tasks = [get_single_kalshi_event(ticker) for ticker in kalshi_tickers]
        all_results = await asyncio.gather(*poly_tasks, *kalshi_tasks)
        
        poly_raw = all_results[:len(poly_slugs)]
        kalshi_raw = all_results[len(poly_slugs):]
        poly_lookup = {}
        for i, slug in enumerate(poly_slugs):
            poly_lookup[slug] = {normalize(m['question']): m for m in poly_raw[i]}
        kalshi_lookup = {}
        for i, ticker in enumerate(kalshi_tickers):
            kalshi_lookup[ticker] = {m['event_ticker']: m for m in kalshi_raw[i]}

        updated_deals = []
        now_str = datetime.now().strftime("%H:%M:%S")

        for deal in deals_list:
            slug = deal['poly'].get('slug')
            series_ticker = deal['kalshi'].get('series_ticker')
            p_q_norm = normalize(deal['poly'].get('question', ''))
            k_ticker = deal['kalshi'].get('event_ticker')

            new_poly = poly_lookup.get(slug, {}).get(p_q_norm)
            new_kalshi = kalshi_lookup.get(series_ticker, {}).get(k_ticker)

            if new_poly and new_kalshi:
                new_arb = calculate_arbitrage(new_poly, new_kalshi, bank=bankroll, min_p_thresh=min_p, max_p_thresh=max_p)
                old_type = deal['arbitrage'].get('type')
                matching = next((a for a in new_arb if a['type'] == old_type), None)
                
                if matching:
                    updated_deals.append({
                        'poly': new_poly, 'kalshi': new_kalshi, 'similarity': deal['similarity'],
                        'arbitrage': matching, 'is_live': True, 'last_update': now_str
                    })
            else:
                if not new_kalshi:
                    print(f"⚠️ [REPARSE] Не найден Kalshi тикер {k_ticker} в серии {series_ticker}")

        print(f"🚀 [LIVE REPARSE] ИТОГ: Обновлено {len(updated_deals)} из {len(deals_list)}")
        return updated_deals

    async def run_scan(self, scan_id: str):
        """Основной цикл сканирования"""
        sl = self.setup_scan_logger(scan_id)
        sl.info(f"🚀 СТАРТ НОВОЙ СЕССИИ: {scan_id}")
        
        try:
            s = await self.get_settings()
            debug_enabled = s.get("DEBUG_MODE", "false").lower() == "true"
            poly_sort = False if s.get("POLY_SORT_BY", "false").lower() == "false" else s.get("POLY_SORT_BY")
            kalshi_sort = False if s.get("KALSHI_SORT_BY", "false").lower() == "false" else s.get("KALSHI_SORT_BY")
            min_price_t = float(s.get("MIN_PRICE_THRESHOLD", 0.10))
            max_price_t = float(s.get("MAX_PRICE_THRESHOLD", 0.90))
            min_profit = float(s.get("MIN_PROFIT", 0.01))
            max_profit = float(s.get("MAX_PROFIT", 100.0))
            bankroll = float(s.get("BANKROLL", 1000))
            total_limit = int(s.get("TOTAL_LIMIT", 5000))
            
            sl.info(f"Настройки: AI={s.get('AI_THRESHOLD', 0.63)}, Bank=${bankroll}, Profit={min_profit}%-{max_profit}%, Limit={total_limit}")
            print(f"\n=======================================================")
            print(f"⚙ТЕКУЩИЕ НАСТРОЙКИ ФИЛЬТРА ПРОФИТА: от {min_profit}% до {max_profit}%")
            print(f"=======================================================\n")
            await self.update_db_status(scan_id=scan_id, progress=10.0, status="fetching_poly")
            sl.info(f"Запрос Polymarket (limit={total_limit}, sort={poly_sort})")
            poly_all = await get_polymarket_politics(total_limit=total_limit, sort_param=poly_sort)
            
            if debug_enabled:
                self.save_debug_json(scan_id, "1_poly_raw", poly_all)
            await self.update_db_status(scan_id=scan_id, progress=30.0, total_poly=len(poly_all), status="fetching_kalshi")
            sl.info(f"Запрос Kalshi (limit={total_limit}, sort={kalshi_sort})")
            kalshi_all = await get_kalshi_politics(total_limit=total_limit, sort_param=kalshi_sort)
            
            if debug_enabled:
                self.save_debug_json(scan_id, "2_kalshi_raw", kalshi_all)
            await self.update_db_status(scan_id=scan_id, progress=50.0, total_kalshi=len(kalshi_all), status="ai_matching")

            if not poly_all or not kalshi_all:
                sl.error("Ошибка: Одна из бирж вернула пустой список.")
                await self.update_db_status(scan_id=scan_id, status="failed: empty_data", progress=0)
                return
            sl.info(f"Запуск HybridMatcher (Threshold: {s.get('AI_THRESHOLD', 0.63)})...")
            matcher = HybridMatcher(threshold=float(s.get('AI_THRESHOLD', 0.63)), use_deepseek=True)
            matcher.index_kalshi(kalshi_all)
            match_results = await matcher.find_matches_batch(poly_all)
            all_matches = match_results["deepseek_verified"]
            
            sl.info(f"AI Мэтчинг завершен. Найдено пар: {len(all_matches)}")
            if debug_enabled:
                self.save_debug_json(scan_id, "3_local_ai_filtered", match_results["local_ai_candidates"])
                self.save_debug_json(scan_id, "4_deepseek_filtered", match_results["deepseek_verified"])
                
            await self.update_db_status(scan_id=scan_id, progress=80.0, total_matches=len(all_matches), status="calculating")
            sl.info("Расчет доходности и временных рамок...")
            arb_opportunities = []
            
            print(f"\n=======================================================")
            print(f" ЭТАП ФИЛЬТРАЦИИ ПРОФИТА (Найдено пар от ИИ: {len(all_matches)})")
            print(f"=======================================================")
            
            for m in all_matches:
                try:
                    results = calculate_arbitrage(
                        m['poly_item'], 
                        m['kalshi_item'], 
                        bank=bankroll,
                        min_p_thresh=min_price_t,
                        max_p_thresh=max_price_t
                    )
                    
                    for arb in results:
                        profit = arb['profit_percent']
                        if min_profit <= profit <= max_profit:
                            print(f"   🟢 ДОБАВЛЕНО В БД: Профит {profit}% попадает в лимиты ({min_profit}% - {max_profit}%)")
                            arb_opportunities.append({
                                'poly': m['poly_item'], 
                                'kalshi': m['kalshi_item'], 
                                'similarity': m['similarity'], 
                                'arbitrage': arb
                            })
                        else:
                            print(f"   🔴 ОТКЛОНЕНО ФИЛЬТРОМ: Профит {profit}% вне лимитов ({min_profit}% - {max_profit}%)")
                except Exception as e:
                    sl.warning(f"Пропущен рынок из-за ошибки математики: {e}")
                    print(f"   ❌ ОШИБКА МАТЕМАТИКИ: {e}")
                    continue
            sl.info(f"Итого отобрано сделок: {len(arb_opportunities)}")
            async with async_session() as session:
                for opp in arb_opportunities:
                    session.add(Deal(
                        scan_id=scan_id,
                        poly_question=opp['poly']['question'],
                        kalshi_question=opp['kalshi']['question'],
                        profit_percent=opp['arbitrage']['profit_percent'],
                        data=opp
                    ))
                await session.commit()
            await self.update_db_status(
                scan_id=scan_id, 
                progress=100.0, 
                status="completed", 
                total_deals=len(arb_opportunities),
                end_time=datetime.utcnow()
            )
            sl.info(f"СЕССИЯ {scan_id} ЗАВЕРШЕНА УСПЕШНО")

        except Exception as e:
            sl.error(f"Критическая ошибка сканера: {e}", exc_info=True)
            await self.update_db_status(scan_id=scan_id, status=f"failed: {str(e)}")
scanner_instance = ArbitrageScanner()