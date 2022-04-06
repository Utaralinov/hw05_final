from django.conf import settings
from django.core.paginator import Paginator


def get_paginator(posts, page):
    paginator = Paginator(posts, settings.PAGE_SIZE)

    return paginator.get_page(page)
