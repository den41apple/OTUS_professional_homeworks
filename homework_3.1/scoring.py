import random

from store import Store


def get_score(store: Store, phone, email, birthday=None, gender=None, first_name=None, last_name=None):
    keys = phone, email, birthday, gender, first_name, last_name
    # Формирование ключа для кеширования в хранилище
    key = ','.join([str(el) for el in keys])
    score = store.cache_get(key) or 0
    score = float(score)
    if score:
        return score
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5
    store.cache_set(key, score, 60*60)  # Сохранение в кеше на 60 минут
    return score


def get_interests(store: Store, cid):
    interests = ["cars", "pets", "travel", "hi-tech", "sport", "music", "books", "tv", "cinema", "geek", "otus"]
    # return random.sample(interests, 2)
    return store.get(f"cid:{cid}") or random.sample(interests, 2)
