from urllib.parse import urlparse

import validators


def validate_url(url):
    if not url:
        return None, 'Заполните это поле'

    if not validators.url(url, public=True):
        return None, 'Некорректный URL'

    normalized_url = normalize_url(url)

    if len(normalized_url) > 255:
        return None, 'URL слишком длинный'

    return normalized_url, None


def normalize_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"