"""
Полезные инструменты
"""
from django.db.models import QuerySet


def make_pagination(queryset: QuerySet,
                     questions_on_page: int = 20,
                     current_page: int = 1) -> dict:
    """
    Подготавливает структуру кнопок пагинации
    """
    pages = {"pages": [],
             "first_page": None,
             "last_page": None,
             "previous_page": None,
             "next_page": None,
             "range": None,
             "_last_page": None}
    _start = (current_page - 1) * questions_on_page
    _end = _start + questions_on_page
    pages['range'] = slice(_start, _end)
    questions_count = queryset.count()
    pages_count = questions_count // questions_on_page

    pages["_last_page"] = pages_count + 1
    if questions_count % questions_on_page != 0:
        pages_count += 1
    if pages_count - current_page >= 3:
        # Будем отображать последнюю страницу
        pages["last_page"] = pages_count

    cur_page = current_page
    for i in range(3):
        if cur_page > pages_count:
            break
        # Добавим предыдущий номер страницы
        if i == 0 and cur_page > 1:
            pages['pages'].append({"number": cur_page - 1,
                                   "is_active": False})

        is_active = False if cur_page != current_page else True
        pages['pages'].append({"number": cur_page,
                               "is_active": is_active})
        cur_page += 1
    # Добавим еще один предыдущий номер если это последняя страница
    if current_page > 2 and current_page == pages_count:
        pages['pages'] = [{"number": current_page - 2,
                           "is_active": False}] + pages['pages']
    if len(pages["pages"]) >= 3 and current_page > 2:
        pages["first_page"] = 1
    # Next page
    if current_page < pages_count:
        pages["next_page"] = current_page + 1
    # Previous page
    if current_page > 1:
        pages["previous_page"] = current_page - 1
    return pages