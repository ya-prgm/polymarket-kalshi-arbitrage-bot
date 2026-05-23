import logging
import httpx
from datetime import datetime
from typing import List, Dict
import re
import asyncio
import faiss

logger = logging.getLogger(__name__)
KALSHI_CATEGORIES = [
    "politics",
    "crypto",
    "financials",
    "Entertainment",
    "Climate and Weather",
    "Science and Technology"
]

def parse_kalshi_date(close_ts):
    """Парсит дату Kalshi для форматированного вывода"""
    try:
        if close_ts:
            if isinstance(close_ts, str):
                dt = datetime.fromisoformat(close_ts.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M UTC')
            dt = datetime.fromtimestamp(int(close_ts))
            return dt.strftime('%Y-%m-%d %H:%M UTC')
    except Exception as e:
        logger.debug(f"Ошибка парсинга даты Kalshi {close_ts}: {e}")
    return 'N/A'

def extract_candidate_from_parentheses(question):
    """Извлекает имя кандидата из скобок Kalshi"""
    match = re.search(r'\(([^)]+)\)', question)
    if match:
        return match.group(1)
    return None

async def get_single_kalshi_event(series_ticker: str, headers=None, proxies=None, use_proxy=False):
    """
    БЫСТРЫЙ ПЕРЕПАРСИНГ (LIVE MODE): 
    Использует эндпоинт v1/events. Сопоставление будет идти по TICKER.
    """
    api_url = f"https://api.elections.kalshi.com/v1/events/?status=open%2Cunopened&series_tickers={series_ticker.upper()}&single_event_per_series=false&tickers=&page_size=100&page_number=1&with_markdown=true"
    
    client_params = {"http2": True, "timeout": 20.0, "verify": False}
    if headers: client_params["headers"] = headers
    if use_proxy and proxies: client_params["proxies"] = proxies

    async with httpx.AsyncClient(**client_params) as client:
        try:
            resp = await client.get(api_url)
            if resp.status_code != 200: return []
            
            data = resp.json()
            events = data.get('events', [])
            if not events: return []
            
            event = events[0]
            event_title = event.get('title', '')
            
            results = []
            for m in event.get('markets', []):
                outcome_name = m.get('yes_subtitle') or m.get('subtitle') or m.get('title') or "Yes"
                last_price = m.get('last_price', 0)
                yes_bid = m.get('yes_bid', 0)
                price_percent = last_price if last_price > 0 else yes_bid
                m_ticker = m.get('ticker_name')
                
                results.append({
                    "question": f"{event_title} ({outcome_name})",
                    "outcomes": {
                        "Yes": f"{price_percent:.1f}%", 
                        "No": f"{100 - price_percent:.1f}%"
                    },
                    "creation_date": m.get('create_date'),
                    "close_date": m.get('close_date'),
                    "event_ticker": m_ticker,
                    "series_ticker": series_ticker,
                    "url": f"https://kalshi.com/markets/{series_ticker.lower()}/{m_ticker.lower()}",
                    "source": "kalshi"
                })
            return results
        except Exception as e:
            logger.error(f"Ошибка Kalshi Reparse {series_ticker}: {e}")
            return []

async def get_kalshi_politics(total_limit=5000, headers=None, proxies=None, use_proxy=False, sort_param=False):
    """
    Парсит ВСЕ категории Kalshi с динамическим распределением лимита.
    Добавлено извлечение дат создания (open_ts) и закрытия (close_ts).
    """
    api_url = "https://api.elections.kalshi.com/v1/search/series"
    all_results = []
    client_params = {
        "http2": True,
        "timeout": 30.0,
        "verify": False
    }
    if headers:
        client_params["headers"] = headers
    if use_proxy and proxies:
        client_params["proxies"] = proxies
    logger.info("\n📊 Получаю количество в каждой категории Kalshi...")
    
    category_counts = {}
    async with httpx.AsyncClient(**client_params) as client:
        for category in KALSHI_CATEGORIES:
            try:
                params = {
                    "category": category,
                    "status": "open,unopened",
                    "page_size": 1,
                    "hydrate": "milestones,structured_targets"
                }
                resp = await client.get(api_url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    total = data.get('total_results_count', 0)
                    category_counts[category] = total
                    logger.info(f"   {category}: {total} серий")
                else:
                    category_counts[category] = 0
            except Exception as e:
                logger.error(f"   {category}: ошибка - {e}")
                category_counts[category] = 0
    active_categories = {cat: count for cat, count in category_counts.items() if count > 0}
    total_active = sum(active_categories.values())
    
    if total_active == 0:
        logger.error("❌ Нет активных категорий в Kalshi")
        return []
    
    logger.info(f"\n📈 Активных категорий Kalshi: {len(active_categories)}, всего серий: {total_active}")
    category_limits = {}
    allocated = 0
    
    for category, count in active_categories.items():
        limit = int(total_limit * (count / total_active))
        limit = max(10, min(limit, 5000))
        category_limits[category] = limit
        allocated += limit
    if allocated < total_limit:
        remaining = total_limit - allocated
        sorted_cats = sorted(active_categories.items(), key=lambda x: x[1], reverse=True)
        for category, _ in sorted_cats:
            if remaining <= 0:
                break
            add = min(remaining, 100)
            category_limits[category] += add
            remaining -= add
    
    logger.info("\n📊 Распределение лимитов Kalshi:")
    for category, limit in category_limits.items():
        logger.info(f"   {category}: {limit} рынков")
    for category in KALSHI_CATEGORIES:
        category_limit = category_limits.get(category, 0)
        if category_limit == 0:
            logger.info(f"⏭️ Пропускаю '{category}' (лимит 0 или нет данных)")
            continue
        
        logger.info(f"\n📌 Kalshi: загружаю категорию '{category}' (лимит {category_limit})")
        
        page_size = 100
        cursor = None
        page_num = 0
        category_results = []
        
        async with httpx.AsyncClient(**client_params) as client:
            while len(category_results) < category_limit:
                page_num += 1
                
                params = {
                    "category": category,
                    "status": "open,unopened",
                    "page_size": page_size,
                    "hydrate": "milestones,structured_targets",
                    "with_milestones": "true"
                }
                if sort_param is not False:
                    params["order_by"] = sort_param
                    params["reverse"] = "false"
                else:
                    params["order_by"] = "trending"
                    params["reverse"] = "true"
                
                if cursor:
                    params["cursor"] = cursor
                
                try:
                    resp = await client.get(api_url, params=params)
                    
                    if resp.status_code != 200:
                        logger.error(f"[!] Ошибка API Kalshi для {category}: {resp.status_code}")
                        break
                    
                    data = resp.json()
                    
                    next_cursor = data.get('next_cursor')
                    series_list = data.get('current_page') or data.get('series', [])
                    
                    for s in series_list:
                        if len(category_results) >= category_limit:
                            break
                        
                        event_title = s.get('event_title', '')
                        event_ticker = s.get('event_ticker', '')
                        series_ticker = s.get('series_ticker', '')
                        
                        for m in s.get('markets', []):
                            if len(category_results) >= category_limit:
                                break
                            
                            outcome_name = m.get('yes_subtitle') or m.get('title') or "Yes"

                            last_price = m.get('last_price')
                            yes_bid = m.get('yes_bid')
                            
                            if last_price and last_price > 0:
                                price_percent = last_price
                            elif yes_bid and yes_bid > 0:
                                price_percent = yes_bid
                            else:
                                price_percent = 0
                            creation_date = m.get('open_ts')
                            close_date = m.get('close_ts')
                            
                            question = f"{event_title} ({outcome_name})"
                            candidate = extract_candidate_from_parentheses(question)
                            
                            if not candidate and outcome_name not in ['Yes', 'No']:
                                candidate = outcome_name
                            
                            category_results.append({
                                "question": question,
                                "candidate": candidate,
                                "outcomes": {
                                    "Yes": f"{price_percent:.1f}%", 
                                    "No": f"{100 - price_percent:.1f}%"
                                },
                                "creation_date": creation_date,
                                "close_date": close_date,
                                "event_ticker": event_ticker,
                                "series_ticker": series_ticker,
                                "close_date_formatted": parse_kalshi_date(close_date),
                                "url": f"https://kalshi.com/markets/{series_ticker}/{event_ticker}" if event_ticker and series_ticker else None,
                                "category": category,
                                "source": "kalshi"
                            })
                    
                    if not next_cursor or len(category_results) >= category_limit:
                        break
                    
                    cursor = next_cursor
                    
                except Exception as e:
                    logger.error(f"[!] Ошибка при загрузке {category}: {e}")
                    break
        
        logger.info(f"   ✅ Категория '{category}': добавлено {len(category_results)} рынков")
        all_results.extend(category_results)
    
    logger.info(f"\n📊 ИТОГО Kalshi: собрано {len(all_results)} рынков")
    return all_results