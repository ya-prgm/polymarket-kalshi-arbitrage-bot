import asyncio
import aiohttp
import json
API_KEY = ""
URL = "https://api.deepseek.com/v1/chat/completions"

async def test_deepseek():
    print("🚀 Запуск тестового запроса к DeepSeek...")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! Reply with 'Connection successful' if you receive this."}
        ],
        "temperature": 0.0,
        "max_tokens": 50
    }
    connector = aiohttp.TCPConnector(ssl=False)
    timeout = aiohttp.ClientTimeout(total=30)

    print("📡 Подключение к серверу (SSL отключен)...")
    
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            print("⏳ Ожидание ответа от API...")
            
            async with session.post(URL, headers=headers, json=payload) as response:
                print(f"📊 Статус код: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    print("\n✅ УСПЕХ! Ответ от нейронки:")
                    print("-" * 40)
                    print(content)
                    print("-" * 40)
                elif response.status == 402:
                    print("\n❌ ОШИБКА 402: Недостаточно средств на балансе DeepSeek!")
                    print(await response.text())
                else:
                    print(f"\n❌ ОШИБКА API: {response.status}")
                    print(await response.text())
                    
    except asyncio.TimeoutError:
        print("\n⏰ ОШИБКА: Таймаут! Сервер DeepSeek не ответил за 30 секунд.")
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА СЕТИ:\n{e}")

if __name__ == "__main__":
    asyncio.run(test_deepseek())