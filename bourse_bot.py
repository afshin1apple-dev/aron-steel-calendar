def get_latest_pages():

    print("=" * 70)
    print("iBROKERS API - DEBUG")
    print("=" * 70)

    session = requests.Session()

    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    })

    all_records = []

    # چند مدل پارامتر را امتحان می‌کنیم
    test_params = [
        {
            "page": 1,
            "limit": 100,
            "sort": "desc"
        },
        {
            "page": 1,
            "limit": 100,
            "sortBy": "id",
            "sortOrder": "desc"
        },
        {
            "page": 1,
            "limit": 100,
            "order": "desc"
        },
        {
            "page": 1,
            "pageSize": 100,
            "sort": "desc"
        },
    ]

    for i, params in enumerate(test_params, 1):

        print()
        print("-" * 70)
        print("TEST:", i)
        print("PARAMS:", params)

        try:

            response = session.get(
                API_URL,
                params=params,
                timeout=30
            )

            print("STATUS:", response.status_code)
            print("URL:", response.url)

            response.raise_for_status()

            data = response.json()

            records = extract_records(data)

            print("RECORDS:", len(records))

            if records:

                for record in records[:5]:

                    print()
                    print("ID:", record_id(record))
                    print("DATE:", record_date_number(record))
                    print("PRODUCT:", get_product(record))
                    print("SUPPLIER:", get_supplier(record))

                    # مهم: تمام فیلدهای رکورد اول
                    if record is records[0]:
                        print()
                        print("FIELDS:")
                        for key, value in record.items():
                            print(
                                f"  {key}: {value}"
                            )

                all_records.extend(records)

        except Exception as e:

            print("ERROR:", e)

    # حذف تکراری‌ها
    unique = {}

    for record in all_records:

        if isinstance(record, dict):
            unique[record_id(record)] = record

    result = list(unique.values())

    print()
    print("=" * 70)
    print("DEBUG TOTAL UNIQUE RECORDS:", len(result))
    print("=" * 70)

    return result