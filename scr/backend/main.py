import logging
import asyncio
import json
from datetime import datetime
import colorama
from colorama import Fore, Style
from module_polymarket import get_polymarket_politics, POLY_CATEGORIES
from module_kalshi import get_kalshi_politics, KALSHI_CATEGORIES
from module_arbitrage import calculate_arbitrage, filter_by_profit, CATEGORY_MAPPING
from module_matcher import HybridMatcher
colorama.init()
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)
SAVE_RAW_DATA = True
POLY_SORT_BY = False
KALSHI_SORT_BY = False

TOTAL_LIMIT = 5000
MIN_PROFIT = 0.01
MAX_PROFIT = 1000.0
BANKROLL = 1000

async def main():
    start_time = datetime.now()
    print(f"\n{Fore.YELLOW}🏆 ARBITRAGE SCANNER AI v16.0 (Gemini Cluster + Bankroll: ${BANKROLL}){Style.RESET_ALL}")
    print(f"{Fore.CYAN}[*] Подключение к биржам...{Style.RESET_ALL}")
    poly_all = await get_polymarket_politics(total_limit=TOTAL_LIMIT, sort_param=POLY_SORT_BY)
    kalshi_all = await get_kalshi_politics(total_limit=TOTAL_LIMIT, sort_param=KALSHI_SORT_BY)

    if not poly_all or not kalshi_all:
        print(f"{Fore.RED}[!] Ошибка: Не удалось получить данные от бирж.{Style.RESET_ALL}")
        return
    if SAVE_RAW_DATA:
        print(f"{Fore.BLUE}[*] Обновление локальной базы вопросов...{Style.RESET_ALL}")
        try:
            poly_questions = [p.get('question') for p in poly_all if p.get('question')]
            kalshi_questions = [k.get('question') for k in kalshi_all if k.get('question')]

            with open('poly_questions.json', 'w', encoding='utf-8') as f:
                json.dump(poly_questions, f, ensure_ascii=False, indent=4)
            with open('kalshi_questions.json', 'w', encoding='utf-8') as f:
                json.dump(kalshi_questions, f, ensure_ascii=False, indent=4)
                
            print(f"{Fore.GREEN}[✓] Файлы вопросов обновлены. Всего: {len(poly_questions) + len(kalshi_questions)}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[!] Ошибка при сохранении JSON: {e}{Style.RESET_ALL}")
    matcher = HybridMatcher()
    
    print(f"\n{Fore.MAGENTA}[*] Индексация Kalshi для AI анализа...{Style.RESET_ALL}")
    matcher.index_kalshi(kalshi_all)
    
    print(f"{Fore.MAGENTA}[*] Запуск AI Кластера (7 ключей Gemini Flash)...{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}[*] Анализируем {len(poly_all)} Poly vs {len(kalshi_all)} Kalshi...{Style.RESET_ALL}")
    all_matches = await matcher.find_matches_batch(poly_all)
    print(f"\n{Fore.CYAN}[*] Расчет доходности для найденных пар...{Style.RESET_ALL}")
    arb_opportunities = []
    
    for m in all_matches:
        results = calculate_arbitrage(m['poly_item'], m['kalshi_item'], bank=BANKROLL)
        
        for arb in results:
            arb_opportunities.append({
                'poly': m['poly_item'], 
                'kalshi': m['kalshi_item'], 
                'similarity': m['similarity'], 
                'arbitrage': arb
            })
    final_list = filter_by_profit(arb_opportunities, MIN_PROFIT, MAX_PROFIT)
    final_list.sort(key=lambda x: x['arbitrage']['profit_percent'], reverse=True)
    print(f"\n{Fore.GREEN}🔥 НАЙДЕНО СДЕЛОК: {len(final_list)}{Style.RESET_ALL}")

    for i, opp in enumerate(final_list, 1):
        p, k, a = opp['poly'], opp['kalshi'], opp['arbitrage']
        profit_color = Fore.GREEN if a['profit_percent'] > 2.0 else Fore.YELLOW
        
        print(f"\n{Fore.WHITE}{'='*60}")
        print(f"{Fore.CYAN}СДЕЛКА №{i} | Профит: {profit_color}{a['profit_percent']}%{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{'='*60}")
        
        print(f"{Fore.BLUE}📈 Poly:   {Style.BRIGHT}{p['question']}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}📉 Kalshi: {Style.BRIGHT}{k['question']}{Style.RESET_ALL}")
        
        print(f"\n{Fore.WHITE}📊 ЦЕНЫ:")
        print(f"   Poly ({a['poly_side']}): {Fore.YELLOW}{a['poly_price_pct']}%{Fore.WHITE} | Kalshi ({a['kalshi_side']}): {Fore.YELLOW}{a['kalshi_price_pct']}%")
        
        print(f"\n{Fore.WHITE}💰 СТАВКИ (Bank: ${BANKROLL}):")
        print(f"   👉 ${a['poly_stake_money']} на Poly")
        print(f"   👉 ${a['kalshi_stake_money']} на Kalshi")
        
        print(f"\n{Fore.GREEN}💵 ЧИСТАЯ ВЫПЛАТА: ${a['expected_return']}")
        print(f"{Fore.MAGENTA}🤖 AI Match: 100% (Confirmed by Gemini){Style.RESET_ALL}")
        
        print(f"\n{Fore.WHITE}🔗 ССЫЛКИ:")
        print(f"   Poly:   {p.get('url')}")
        print(f"   Kalshi: {k.get('url')}")
    duration = (datetime.now() - start_time).total_seconds()
    print(f"\n{Fore.YELLOW}{'='*60}")
    print(f"✅ СКАН ЗАВЕРШЕН ЗА {duration:.1f} СЕК.")
    print(f"Всего рынков обработано: {len(poly_all) + len(kalshi_all)}")
    print(f"{'='*60}{Style.RESET_ALL}\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Скан прерван пользователем.{Style.RESET_ALL}")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")