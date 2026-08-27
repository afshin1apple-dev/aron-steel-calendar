from pivan import get_prices


prices = get_prices()


print("=" * 60)
print("PIVAN FINAL PRICE RESULT")
print("=" * 60)


for item in prices:

    if item["price"] is None:
        price = "تماس بگیرید"
    else:
        price = f'{item["price"]:,}'

    print(
        f'میلگرد {item["size"]} '
        f'{item["standard"]} '
        f'→ {price} تومان'
    )


print()
print(f"TOTAL: {len(prices)}")