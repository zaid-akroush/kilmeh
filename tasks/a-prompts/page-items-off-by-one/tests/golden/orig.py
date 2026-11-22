def get_page(items, page, per_page):
    start = page * per_page
    end = start + per_page
    return items[start:end]
