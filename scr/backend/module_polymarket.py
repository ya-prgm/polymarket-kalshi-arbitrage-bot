import logging
import httpx
import json
from datetime import datetime
from typing import List, Dict
import asyncio
import faiss

logger = logging.getLogger(__name__)
POLY_CATEGORIES = [
    "politics",
    "crypto", 
    "finance",
    "pop-culture",
    "climate-science",
    "tech"
]

def parse_polymarket_date(end_date_str):
    """Парсит дату Polymarket для форматированного вывода"""
    try:
        if end_date_str:
            dt = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M UTC')
    except Exception as e:
        logger.debug(f"Ошибка парсинга даты Polymarket {end_date_str}: {e}")
    return 'N/A'

def extract_candidate_name(question):
    """Извлекает имя кандидата из вопроса Polymarket"""
    import re
    match = re.search(r'Will\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+win', question)
    if match:
        return match.group(1)
    match = re.search(r'([A-Z][a-z]+ [A-Z][a-z]+)(?:\s+to|\s+be|\s+win)', question)
    if match:
        return match.group(1)
    return None

async def get_single_polymarket_event(slug: str, proxies=None, use_proxy=False):
    """
    БЫСТРЫЙ ПЕРЕПАРСИНГ: Получает данные только по одному конкретному событию Polymarket по его слагу.
    Используется для Live-обновления цен в уже найденных вилках.
    """
    api_url = f"https://gamma-api.polymarket.com/events?slug={slug}"
    
    client_params = {
        "timeout": 20.0,
        "verify": False
    }
    if use_proxy and proxies:
        client_params["proxies"] = proxies

    async with httpx.AsyncClient(**client_params) as client:
        try:
            resp = await client.get(api_url)
            if resp.status_code != 200:
                logger.error(f"Ошибка API Poly при перепарсинге {slug}: {resp.status_code}")
                return []
            
            data = resp.json()
            if not data or not isinstance(data, list):
                return []
            event = data[0]
            event_slug = event.get('slug', '')
            creation_date = event.get('creationDate') or event.get('createdAt')
            end_date_event = event.get('endDate')
            markets = event.get('markets', [])
            
            results = []
            for market in markets:
                question = market.get('question', '')
                close_date = market.get('endDate') or end_date_event
                outcomes = market.get('outcomes', [])
                outcome_prices_str = market.get('outcomePrices', '[]')
                
                candidate = extract_candidate_name(question)
                outcome_map = {}
                
                try:
                    if isinstance(outcome_prices_str, str):
                        outcome_prices = json.loads(outcome_prices_str)
                    else:
                        outcome_prices = outcome_prices_str
                    
                    if isinstance(outcomes, str):
                        outcomes_list = json.loads(outcomes)
                    else:
                        outcomes_list = outcomes
                    
                    if outcome_prices and len(outcome_prices) > 0:
                        for i, name in enumerate(outcomes_list):
                            if i < len(outcome_prices):
                                price = float(outcome_prices[i])
                                outcome_map[name] = f"{price*100:.1f}%"
                except Exception as e:
                    continue

                if 'Yes' in outcome_map and 'No' not in outcome_map:
                    try:
                        yes_price = float(outcome_map['Yes'].rstrip('%')) / 100
                        outcome_map['No'] = f"{(1.0 - yes_price)*100:.1f}%"
                    except: pass

                results.append({
                    "question": question,
                    "candidate": candidate,
                    "outcomes": outcome_map,
                    "creation_date": creation_date,
                    "close_date": close_date,
                    "slug": event_slug,
                    "end_date_formatted": parse_polymarket_date(close_date),
                    "url": f"https://polymarket.com/event/{event_slug}",
                    "source": "polymarket"
                })
            return results
        except Exception as e:
            logger.error(f"Критическая ошибка перепарсинга Poly {slug}: {e}")
            return []

async def get_polymarket_politics(total_limit=5000, proxies=None, use_proxy=False, sort_param=False):
    """
    Парсит ВСЕ категории Polymarket с динамическим распределением лимита.
    Добавлено извлечение дат создания и закрытия.
    """
    api_url = "https://gamma-api.polymarket.com/events/pagination"
    all_results = []
    client_params = {
        "timeout": 30.0,
        "verify": False
    }
    if use_proxy and proxies:
        client_params["proxies"] = proxies
    logger.info("📊 Получаю количество событий в каждой категории Polymarket...")
    
    category_counts = {}
    async with httpx.AsyncClient(**client_params) as client:
        for category in POLY_CATEGORIES:
            try:
                params = {
                    "limit": 1,
                    "active": "true",
                    "archived": "false",
                    "tag_slug": category,
                    "closed": "false"
                }
                
                resp = await client.get(api_url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict) and 'pagination' in data:
                        total = data['pagination'].get('totalResults', 0)
                        category_counts[category] = total
                        logger.info(f"   {category}: {total} событий")
                    else:
                        category_counts[category] = 0
                else:
                    logger.warning(f"   {category}: статус {resp.status_code}")
                    category_counts[category] = 0
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"   {category}: ошибка - {e}")
                category_counts[category] = 0
    total_available = sum(category_counts.values())
    logger.info(f"\n📈 Всего доступно событий Polymarket: {total_available}")
    
    if total_available == 0:
        logger.error("❌ Нет доступных событий ни в одной категории Polymarket")
        return []
    category_limits = {}
    allocated = 0
    for category, count in category_counts.items():
        if count > 0:
            limit = int(total_limit * (count / total_available))
            limit = max(10, min(limit, 10000))
            category_limits[category] = limit
            allocated += limit
        else:
            category_limits[category] = 0
    if allocated < total_limit and total_available > 0:
        remaining = total_limit - allocated
        sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        for category, _ in sorted_cats:
            if remaining <= 0:
                break
            if category_limits[category] > 0:
                add = min(remaining, 100)
                category_limits[category] += add
                remaining -= add
    
    logger.info("\n📊 Распределение лимитов Polymarket:")
    for category, limit in category_limits.items():
        if limit > 0:
            logger.info(f"   {category}: {limit} рынков")
    for category in POLY_CATEGORIES:
        category_limit = category_limits.get(category, 0)
        if category_limit == 0:
            logger.info(f"⏭️ Пропускаю '{category}' (лимит 0)")
            continue
        
        logger.info(f"\n📌 Polymarket: загружаю категорию '{category}' (лимит {category_limit})")
        
        offset = 0
        category_results = []
        
        while len(category_results) < category_limit:
            params = {
                "limit": min(100, category_limit - len(category_results)),
                "active": "true",
                "archived": "false",
                "tag_slug": category,
                "closed": "false",
                "offset": offset
            }
            if sort_param is not False:
                params["order"] = sort_param
                params["ascending"] = "true"
            else:
                params["order"] = "volume24hr"
                params["ascending"] = "false"
            
            page_success = False
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    client_params = {
                        "timeout": 60.0,
                        "verify": False
                    }
                    if use_proxy and proxies:
                        client_params["proxies"] = proxies
                    
                    async with httpx.AsyncClient(**client_params) as client:
                        resp = await client.get(api_url, params=params)
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            events = []
                            
                            if isinstance(data, dict) and 'data' in data:
                                events = data.get('data', [])
                            
                            if not events:
                                page_success = True
                                break
                                
                            for event in events:
                                if not isinstance(event, dict):
                                    continue
                                creation_date = event.get('creationDate') or event.get('createdAt')
                                event_slug = event.get('slug', '')
                                end_date_event = event.get('endDate')
                                markets = event.get('markets', [])
                                
                                for market in markets:
                                    if len(category_results) >= category_limit:
                                        break
                                    
                                    if not isinstance(market, dict):
                                        continue
                                    
                                    question = market.get('question', '')
                                    close_date = market.get('endDate') or end_date_event
                                    
                                    outcomes = market.get('outcomes', [])
                                    outcome_prices_str = market.get('outcomePrices', '[]')
                                    
                                    candidate = extract_candidate_name(question)
                                    
                                    outcome_map = {}
                                    
                                    try:
                                        if isinstance(outcome_prices_str, str):
                                            outcome_prices = json.loads(outcome_prices_str)
                                        else:
                                            outcome_prices = outcome_prices_str
                                        
                                        if isinstance(outcomes, str):
                                            outcomes_list = json.loads(outcomes)
                                        else:
                                            outcomes_list = outcomes
                                        
                                        if outcome_prices and len(outcome_prices) > 0:
                                            for i, name in enumerate(outcomes_list):
                                                if i < len(outcome_prices):
                                                    price = float(outcome_prices[i])
                                                    outcome_map[name] = f"{price*100:.1f}%"
                                        
                                    except Exception as e:
                                        continue
                                    
                                    if 'Yes' in outcome_map and 'No' not in outcome_map:
                                        try:
                                            yes_price = float(outcome_map['Yes'].rstrip('%')) / 100
                                            outcome_map['No'] = f"{(1.0 - yes_price)*100:.1f}%"
                                        except: pass
                                    
                                    if not outcome_map:
                                        continue
                                    
                                    category_results.append({
                                        "question": question,
                                        "candidate": candidate,
                                        "outcomes": outcome_map,
                                        "creation_date": creation_date,
                                        "close_date": close_date,
                                        "slug": event_slug,
                                        "end_date_formatted": parse_polymarket_date(close_date),
                                        "url": f"https://polymarket.com/event/{event_slug}" if event_slug else None,
                                        "category": category,
                                        "source": "polymarket"
                                    })
                            
                            offset += len(events)
                            page_success = True
                            logger.info(f"   → Собрано {len(category_results)}/{category_limit}...")
                            break
                            
                        elif resp.status_code == 500 and attempt < max_retries - 1:
                            logger.warning(f"   ⚠️ Ошибка 500, попытка {attempt + 2}/{max_retries} через 2 секунды...")
                            await asyncio.sleep(2)
                            continue
                        else:
                            logger.error(f"[!] Ошибка API для {category}: {resp.status_code}")
                            break
                            
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"   ⚠️ Ошибка: {e}, попытка {attempt + 2}/{max_retries} через 2 секунды...")
                        await asyncio.sleep(2)
                    else:
                        logger.error(f"[!] Ошибка при загрузке {category}: {e}")
            
            if not page_success or not events:
                break
                
        logger.info(f"   ✅ Категория '{category}': добавлено {len(category_results)} рынков")
        all_results.extend(category_results)
    
    logger.info(f"\n📊 ИТОГО Polymarket: собрано {len(all_results)} рынков")
    return all_results