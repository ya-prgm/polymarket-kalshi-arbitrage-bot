

import asyncio
import json
import logging
import re
import numpy as np
import aiohttp
from datetime import datetime
from typing import List, Dict
from sentence_transformers import SentenceTransformer, util

try:
    from categories import detect_category
except ImportError:
    def detect_category(text: str) -> str: return "other"

logger = logging.getLogger(__name__)

DEEPSEEK_API_KEY = ""
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


def clean_and_normalize(text: str) -> str:
    t = text.lower()
    t = t.replace('(', ' ').replace(')', ' ')
    t = re.sub(r'(\d+)\s?k\b', r'\1000', t)
    t = re.sub(r'(\d+),(\d+)', r'\1\2', t)
    t = re.sub(r'(\d+\.\d*?[1-9])0+\b|(\d+\.0+)\b', r'\1\2', t)
    t = re.sub(r'[^a-z0-9\s\.\$]', ' ', t)
    return ' '.join(t.split())


def check_hard_conflicts(p_text: str, k_text: str) -> bool:
    p = p_text.lower()
    k = k_text.lower()

    assets = ['bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'sol', 'xrp', 'bnb', 'megaeth', 'cardano']
    for asset in assets:
        if (asset in p) != (asset in k):
            return True

    names = ['trump', 'biden', 'vance', 'harris', 'musk', 'bieber', 'swift', 'epstein', 'drake']
    for name in names:
        if (name in p) != (name in k):
            return True

    actions_politics = ['win', 'nomination', 'nominee', 'elected', 'primary']
    actions_legal = ['epstein', 'files', 'charged', 'crime', 'repeal', 'lawsuit', 'leave', 'expelled']
    
    p_is_politics = any(a in p for a in actions_politics)
    k_is_legal = any(a in k for a in actions_legal)
    p_is_legal = any(a in p for a in actions_legal)
    k_is_politics = any(a in k for a in actions_politics)

    if (p_is_politics and k_is_legal) or (p_is_legal and k_is_politics):
        return True

    return False


class DeepSeekBatchVerifier:
    def __init__(self, max_concurrent: int = 3):
        self.api_key = DEEPSEEK_API_KEY
        self.api_url = DEEPSEEK_API_URL
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def _call_deepseek(self, prompt: str, timeout: int = 150, max_retries: int = 3) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a financial analyst. Answer ONLY with comma-separated indices or 'NONE'."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0,
            "max_tokens": 500
        }
        connector = aiohttp.TCPConnector(ssl=False)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            for attempt in range(max_retries):
                try:
                    async with session.post(self.api_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            full_response = data['choices'][0]['message']['content']
                            
                            print(f"\n   📨 ПОЛНЫЙ ОТВЕТ DEEPSEEK (Попытка {attempt + 1}):")
                            print(f"   {'='*60}")
                            for line in full_response.split('\n')[:10]:
                                print(f"   {line}")
                            print(f"   {'='*60}\n")
                            
                            return full_response.strip().upper()
                        elif resp.status == 429:
                            print(f"   ⏳ DeepSeek Rate Limit (429). Ждем {5 * (attempt + 1)} сек...")
                            await asyncio.sleep(5 * (attempt + 1))
                        else:
                            error_text = await resp.text()
                            print(f"   ❌ DeepSeek ошибка {resp.status}: {error_text[:200]}")
                            
                except asyncio.TimeoutError:
                    print(f"   ⏰ Таймаут DeepSeek (Попытка {attempt + 1}/{max_retries})")
                except Exception as e:
                    print(f"   ❌ Ошибка сети/SSL (Попытка {attempt + 1}/{max_retries}): {str(e)[:150]}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)
            
            print("   ⚠️ Все попытки исчерпаны. Возвращаем NONE.")
            return "NONE"

    async def verify_batch(self, pairs: List[Dict]) -> List[bool]:
        if not pairs:
            return []
        
        prompt_lines = []
        for idx, pair in enumerate(pairs):
            poly_q = pair['poly_item'].get('question', '')[:150]
            kalshi_q = pair['kalshi_item'].get('question', '')[:150]
            prompt_lines.append(f"[{idx}] Poly: {poly_q}")
            prompt_lines.append(f"    Kalshi: {kalshi_q}")
        
        current_date = datetime.now().strftime("%B %d, %Y")
        
        prompt = f"""You are a Senior Arbitrage Analyst. Today is {current_date}.
Compare pairs of prediction market questions for 100% mathematical fungibility.

CONTEXTUAL RULES FOR {current_date[-4:]}:
1. TIMEFRAME MATCH: Since today is {current_date}, references to "this year", "in {current_date[-4:]}", and "before {int(current_date[-4:])+1}" are IDENTICAL. If both markets end on the exact same date, answer YES.
2. SCOPE MISMATCH (CRITICAL): "DHS shutdown" is NOT "Government shutdown". "NYC visit" is NOT "New York State visit". If one is a subset of the other, answer NO.
3. RESOLUTION LOGIC: "Where will they NEXT meet?" (no deadline) is NOT the same as "Will they meet BEFORE {int(current_date[-4:])+1}?". One is perpetual, the other is time-bound. Answer NO.
4. EXACT ENTITY: "Donald Trump" is NOT "Donald Trump Jr". "Nominated" is NOT "Confirmed" (unless the question specifically asks for the same result).
5. PRICE LEVELS: Bitcoin "Dip to $60k" is NOT "Dip to $58k". Targets must be identical to 0.01 precision.

ARBITRAGE TEST:
If I bet YES on Market A and NO on Market B, is there ANY scenario (even 0.1% chance) where I lose both bets? 
- If YES (risk exists), answer NO.
- If NO (zero risk), answer YES.
Если ты видишь что-то вроде 📈 Poly: Will Trump visit China by May 31? 📉 Kalshi: When will Trump visit China? (Before May 15), ОТВЕЧАЙ НЕТ, ТАК КАК ДАТЫ НЕ СООТВЕТСТВУЮТ. ЭТО БУДЕТ ПРОВАЛ!

PAIRS TO EVALUATE:
{chr(10).join(prompt_lines)}

Return ONLY a comma-separated list of indices that are YES. Example: 0, 5, 12.
If no 100% matches found, return 'NONE'.
"""
        
        print(f"   📡 Отправка пачки {len(pairs)} пар в DeepSeek...")
        result_text = await self._call_deepseek(prompt, timeout=150)
        
        if "NONE" in result_text or not result_text:
            print(f"   ⚠️ DeepSeek вернул NONE или пустой ответ для этой пачки")
            return [False] * len(pairs)
        
        matched_indices = set()
        for part in result_text.replace(',', ' ').split():
            try:
                matched_indices.add(int(part))
            except ValueError:
                nums = re.findall(r'\d+', part)
                for n in nums:
                    matched_indices.add(int(n))
        
        print(f"   ✅ Найдены индексы: {sorted(matched_indices)}")
        return [i in matched_indices for i in range(len(pairs))]

    async def verify_batches_parallel(self, batches: List[List[Dict]]) -> List[List[bool]]:
        if not batches:
            return []
        
        print(f"   🚀 Запуск параллельной обработки {len(batches)} пачек (concurrent={self.semaphore._value})")
        
        async def process_batch_with_semaphore(batch):
            async with self.semaphore:
                return await self.verify_batch(batch)
        
        tasks = [process_batch_with_semaphore(batch) for batch in batches]
        results = await asyncio.gather(*tasks)
        
        return results


class HybridMatcher:
    def __init__(self, threshold: float = 0.63, use_deepseek: bool = True, max_concurrent: int = 3):
        self.threshold = threshold
        self.use_deepseek = use_deepseek
        self.max_concurrent = max_concurrent
        self.model = None
        self.kalshi_data = []
        self.kalshi_embeddings = None
        self.deepseek = DeepSeekBatchVerifier(max_concurrent=max_concurrent) if use_deepseek else None

    def index_kalshi(self, kalshi_items: List[Dict]):
        if not kalshi_items: return
        
        print("   🤖 Инициализация MiniLM модели...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        processed = []
        for item in kalshi_items:
            q = item['question']
            processed.append({
                'original': item,
                'norm': clean_and_normalize(q),
                'cat': detect_category(q)
            })
        
        self.kalshi_data = processed
        self.kalshi_embeddings = self.model.encode(
            [x['norm'] for x in processed], 
            normalize_embeddings=True,
            show_progress_bar=False
        )

    async def find_matches_batch(self, poly_items: List[Dict]) -> Dict:
        if not self.model: return {"local_ai_candidates": [], "deepseek_verified": []}
        
        print(f"   🔢 Вычисление эмбеддингов для {len(poly_items)} вопросов...")
        
        poly_processed = []
        for item in poly_items:
            q = item['question']
            poly_processed.append({
                'original': item,
                'norm': clean_and_normalize(q),
                'cat': detect_category(q)
            })
            
        poly_embeddings = self.model.encode([p['norm'] for p in poly_processed], normalize_embeddings=True)
        cosine_scores = util.cos_sim(poly_embeddings, self.kalshi_embeddings).cpu().numpy()
        
        candidates = []
        
        for i, p_info in enumerate(poly_processed):
            top_indices = np.argsort(cosine_scores[i])[-15:][::-1]
            
            for k_idx in top_indices:
                k_info = self.kalshi_data[k_idx]
                score = float(cosine_scores[i][k_idx])
                
                p_text_raw = p_info['original']['question']
                k_text_raw = k_info['original']['question']

                if p_info['cat'] != k_info['cat']:
                    continue
                if check_hard_conflicts(p_text_raw, k_text_raw):
                    continue
                if score >= self.threshold:
                    candidates.append({
                        'poly_item': p_info['original'],
                        'kalshi_item': k_info['original'],
                        'similarity': score,
                        'poly_cat': p_info['cat']
                    })
                    break
        
        print(f"   📊 Кандидатов после быстрых фильтров (MiniLM): {len(candidates)}")
        
        if not candidates:
            return {"local_ai_candidates": [], "deepseek_verified": []}
        
        if self.use_deepseek and self.deepseek:
            print(f"   🤖 Пакетная верификация через DeepSeek (ЭТАП 1)...")
            
            batch_size = 15
            batches_stage_1 = []
            for batch_start in range(0, len(candidates), batch_size):
                batches_stage_1.append(candidates[batch_start:batch_start + batch_size])
            
            print(f"   📦 Создано {len(batches_stage_1)} пачек для Этапа 1")
            batch_results_1 = await self.deepseek.verify_batches_parallel(batches_stage_1)
            
            verified_stage_1 = []
            for batch_idx, results in enumerate(batch_results_1):
                for pair_idx, is_match in enumerate(results):
                    if is_match:
                        verified_stage_1.append(batches_stage_1[batch_idx][pair_idx])
            
            print(f"\n   ✅ После Этапа 1: {len(verified_stage_1)}/{len(candidates)} пар подтверждены")
            if verified_stage_1:
                print(f"\n   🕵️‍♂️ ДВОЙНАЯ ВЕРИФИКАЦИЯ через DeepSeek (ЭТАП 2)...")
                batches_stage_2 = []
                for batch_start in range(0, len(verified_stage_1), batch_size):
                    batches_stage_2.append(verified_stage_1[batch_start:batch_start + batch_size])
                
                print(f"   📦 Создано {len(batches_stage_2)} пачек для Этапа 2")
                batch_results_2 = await self.deepseek.verify_batches_parallel(batches_stage_2)
                
                verified_stage_2 = []
                for batch_idx, results in enumerate(batch_results_2):
                    for pair_idx, is_match in enumerate(results):
                        if is_match:
                            verified_stage_2.append(batches_stage_2[batch_idx][pair_idx])
                
                print(f"\n   🛡️ После Этапа 2 (Финальный фильтр): {len(verified_stage_2)}/{len(verified_stage_1)} пар подтверждены")
                final_matches = verified_stage_2
            else:
                final_matches = []
        else:
            final_matches = candidates
        final_matches.sort(key=lambda x: -x['similarity'])
        seen = set()
        unique = []
        for m in final_matches:
            k_q = m['kalshi_item']['question']
            if k_q not in seen:
                seen.add(k_q)
                unique.append(m)
        
        print(f"\n🔍 [AI MATCHING] Найдено чистых пар: {len(unique)}")
        print("-" * 60)
        for idx, m in enumerate(unique[:15]):
            sim_pct = m['similarity'] * 100
            print(f"{idx+1}. [{sim_pct:.1f}%] [{m['poly_cat']}]")
            print(f"   P: {m['poly_item']['question'][:100]}")
            print(f"   K: {m['kalshi_item']['question'][:100]}\n")
        print("-" * 60)
        return {
            "local_ai_candidates": candidates,
            "deepseek_verified": unique
        }


if __name__ == "__main__":
    test_q = "Will Bitcoin reach $250k before 2027?"
    print(f"Normalize Test: {clean_and_normalize(test_q)}")