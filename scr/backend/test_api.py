import requests
import time
import sys
from colorama import Fore, Style, init

init(autoreset=True)
URL = "http://127.0.0.1:8000"

def test():
    print(f"{Fore.MAGENTA}=== ЗАПУСК ТЕСТА API ===")
    print(f"[*] Ресурсы: {requests.get(f'{URL}/api/system/stats').json()}")
    print(f"[*] Баланс DeepSeek: {requests.get(f'{URL}/api/deepseek/balance').json()}")
    print(f"[*] Обновление настроек (Debug=True, Sort=endDate)...")
    requests.post(f"{URL}/api/settings", json={
        "DEBUG_MODE": "true",
        "POLY_SORT_BY": "endDate",
        "KALSHI_SORT_BY": "closing",
        "AI_THRESHOLD": "0.70"
    })
    start = requests.post(f"{URL}/api/scan/start").json()
    sid = start['scan_id']
    print(f"{Fore.GREEN}[+] Скан запущен! ID: {sid}")
    while True:
        status = requests.get(f"{URL}/api/scan/status/{sid}").json()
        prog = status['progress']
        msg = status['status']
        sys.stdout.write(f"\r   Прогресс: {prog}% | Статус: {Fore.YELLOW}{msg} ")
        sys.stdout.flush()
        
        if status['status'] == 'completed': 
            print(f"\n{Fore.GREEN}[✓] Завершено!")
            break
        if 'failed' in status['status']:
            print(f"\n{Fore.RED}[×] Ошибка!")
            break
        time.sleep(2)
    deals = requests.get(f"{URL}/api/scan/results/{sid}").json()
    print(f"[*] Найдено сделок: {len(deals)}")
    print(f"[*] Ссылка на лог: {URL}/api/scan/log/{sid}")

if __name__ == "__main__":
    test()