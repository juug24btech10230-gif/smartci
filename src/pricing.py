def apply_discount(price, percent):
    if not 0 <= percent <= 100:
        raise ValueError('percent must be between 0 and 100')
    return round(price * (1 - percent / 100), 2)


def add_tax(price, rate=0.18):
    return round(price * (1 + rate), 2)


def bulk_discount(price, qty):
    rate = 10 if qty >= 10 else 0
    return apply_discount(price * qty, rate)
