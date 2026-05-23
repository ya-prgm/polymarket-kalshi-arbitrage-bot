import logging
from datetime import datetime

logger = logging.getLogger(__name__)
CATEGORY_MAPPING = {
    "politics": ["politics"],
    "crypto": ["crypto"],
    "finance": ["financials"],
    "pop-culture": ["Entertainment"],
    "climate-science": ["Climate and Weather"],
    "tech": ["Science and Technology"],
}

def get_price(item, side="Yes"):
    """Извлекает цену исхода и переводит в decimal (0.0 - 1.0)"""
    outcomes = item.get('outcomes', {})
    if side in outcomes:
        try:
            return float(outcomes[side].rstrip('%')) / 100
        except: 
            return None
    if side == "Yes" and outcomes:
        try:
            first_key = list(outcomes.keys())[0]
            return float(outcomes[first_key].rstrip('%')) / 100
        except: 
            return None
    return None

def parse_universal_date(date_val):
    """
    Парсит и ISO строки (Polymarket), и Unix Timestamps (Kalshi).
    Возвращает объект datetime без таймзоны.
    """
    if not date_val:
        return None
    try:
        if isinstance(date_val, (int, float)):
            return datetime.fromtimestamp(date_val)
        if isinstance(date_val, str):
            if date_val.isdigit():
                return datetime.fromtimestamp(int(date_val))
            return datetime.fromisoformat(date_val.replace('Z', '+00:00')).replace(tzinfo=None)
    except Exception as e:
        logger.debug(f"Ошибка парсинга даты {date_val}: {e}")
    return None

def calculate_arbitrage(poly_item, kalshi_item, bank=1000, min_p_thresh=0.01, max_p_thresh=0.99):
    """
    Расчет арбитражной ситуации по классической букмекерской формуле.
    Возвращает результат ВСЕГДА, без фильтрации по Sp < 1 и без фильтрации по ценам.
    """
    opportunities = []
    now = datetime.utcnow()
    
    print(f"\n[MATH DEBUG] Анализ пары:")
    print(f"   P: {poly_item.get('question')} | Исход: {poly_item.get('outcomes')}")
    print(f"   K: {kalshi_item.get('question')} | Исход: {kalshi_item.get('outcomes')}")
    p_created = parse_universal_date(poly_item.get('creation_date'))
    p_closed = parse_universal_date(poly_item.get('close_date'))
    k_created = parse_universal_date(kalshi_item.get('creation_date'))
    k_closed = parse_universal_date(kalshi_item.get('close_date'))

    if p_closed and k_closed:
        final_close = p_closed if p_closed < k_closed else k_closed
    else:
        final_close = p_closed or k_closed

    days_remaining = 0
    if final_close:
        delta = final_close - now
        days_remaining = max(0, delta.days)
    p_yes = get_price(poly_item, "Yes")
    k_yes = get_price(kalshi_item, "Yes")
    
    if p_yes is None or k_yes is None or p_yes <= 0 or k_yes <= 0: 
        print(f"   ❌ ОТКЛОНЕНО (Нет цен или формат не Yes/No). p_yes={p_yes}, k_yes={k_yes}")
        return []

    p_no = 1.0 - p_yes
    k_no = 1.0 - k_yes
    scenarios = [
        {"name": "POLY Yes + KALSHI No", "p1": p_yes, "p2": k_no, "s1": "Yes", "s2": "No"},
        {"name": "POLY No + KALSHI Yes", "p1": p_no, "p2": k_yes, "s1": "No", "s2": "Yes"}
    ]

    for sc in scenarios:
        p1 = sc["p1"]
        p2 = sc["p2"]
        if p1 <= 0.0001 or p2 <= 0.0001 or p1 >= 0.9999 or p2 >= 0.9999:
            print(f"   ⚠️ ПРОПУСК СЦЕНАРИЯ '{sc['name']}': Сработала защита от деления на ноль (цена 0% или 100%). p1={p1}, p2={p2}")
            continue
        k1 = 1 / p1
        k2 = 1 / p2
        sp = (1 / k1) + (1 / k2)
        profit_pct = (1 - sp) * 100
        s1 = bank / (k1 * sp)
        s2 = bank / (k2 * sp)
        
        print(f"   ✅ Рассчитан сценарий '{sc['name']}': Профит = {profit_pct:.2f}% (Sp={sp:.3f})")
        opportunities.append({
            'type': sc["name"],
            'profit_percent': round(profit_pct, 2),
            'days_remaining': days_remaining,
            'sp': round(sp, 3),
            'poly_price_pct': round(p1 * 100, 1),
            'kalshi_price_pct': round(p2 * 100, 1),
            'poly_side': sc["s1"],
            'kalshi_side': sc["s2"],
            'poly_stake_money': round(s1, 2),
            'kalshi_stake_money': round(s2, 2),
            'expected_return': round(s1 * k1, 2),
            'market_dates': {
                'poly_created': p_created.strftime('%Y-%m-%d') if p_created else "N/A",
                'poly_closed': p_closed.strftime('%Y-%m-%d') if p_closed else "N/A",
                'kalshi_created': k_created.strftime('%Y-%m-%d') if k_created else "N/A",
                'kalshi_closed': k_closed.strftime('%Y-%m-%d') if k_closed else "N/A",
                'final_close_date': final_close.strftime('%Y-%m-%d') if final_close else "N/A"
            }
        })
        
    if opportunities:
        opportunities.sort(key=lambda x: x['profit_percent'], reverse=True)
        print(f"   🏆 Выбран лучший сценарий с профитом {opportunities[0]['profit_percent']}%")
        return [opportunities[0]]
        
    return []

def filter_by_profit(opportunities, min_profit=0.01, max_profit=100.0):
    """Фильтрация списка найденных сделок по проценту доходности"""
    return [opp for opp in opportunities if min_profit <= opp['arbitrage']['profit_percent'] <= max_profit]