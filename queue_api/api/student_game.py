from .imports import *
import numpy as np

DAY_MAX = 30


def already_played(date1: datetime, date2: datetime):
    return date1.day == date2.day


def check_session_time(date1: datetime, date2: datetime):
    date1 = date1.replace(hour=0, minute=0, second=0, microsecond=0)
    date2 = date2.replace(hour=0, minute=0, second=0, microsecond=0)
    return date2 - date1 >= timedelta(weeks=1)


def norm_distr(mu: float, sigma: float):
    rng = np.random.default_rng()
    return rng.normal(mu, sigma)


async def change_rating(user_id: int, group_id: int):
    student_group, _ = await StudentGroup.objects.aget_or_create(group_id=group_id)
    group_member = await GroupMember.objects.aget(user_id=user_id, groups_id=group_id)
    student, is_created = await Student.objects.aget_or_create(group_member_id=group_member.pk)
    if is_created:
        return f"Ну поживи как-нибудь на 100 рублей в месяц, авось не сдохнешь с голоду"
    if already_played(timezone.now(), student.date):
        return f"Пары сегодня закончились, приходите завтра"
    else:
        mu, sigma = 0, DAY_MAX / 3 - 1
        delta = norm_distr(mu, sigma)
        student.rating = F('rating') + delta
        await student.asave()
        if delta < 0:
            return f"Схватил двойку по типовику Дзержа - ЛОХ хаххахахаха.\nВаш рейтинг уменьшился на {delta} единиц и стал равен {student.rating}"
        return f"Насосал, получается)))))\nВаш рейтинг увеличился на {delta} единиц и стал равен {student.rating}"


def normalize(value: float, _min: float, _max: float):
    return (value - _min) / (_max - _min)


async def change_scholarship(user_id: int, group_id: int):
    group_member = await GroupMember.objects.aget(user_id=user_id, groups_id=group_id)
    student, is_created = await Student.objects.aget_or_create(group_member_id=group_member.pk)
    rating = student.rating
    prev_rating = student.prev_rating
    delta_rating = rating - prev_rating
    normalized_delta_rating = normalize(delta_rating, -DAY_MAX * 14, DAY_MAX * 14)
    mu = student.scholarship * normalized_delta_rating
    delta = student.scholarship * normalized_delta_rating / 3
    delta_scholarship = norm_distr(mu, delta)
    if delta_rating <= 0:
        student.scholarship = F('scholarship') - delta_scholarship
        await student.asave()
        text = f"Схлопотал двоек на сессии, теперь страдай без стипендии! Она стала равной {student.scholarship} р."
    else:
        student.scholarship = F('scholarship') + delta_scholarship
        await student.asave()
        text = f"Всем преподавателям угодил, стипендия увеличилась! Она стала равной {student.scholarship} р."
    return text


async def print_places(user_id: int, group_id: int):
    group_member = await GroupMember.objects.aget(user_id=user_id, groups_id=group_id)
    student, _ = await Student.objects.aget_or_create(group_member_id=group_member.pk)
    rating, scholarship = student.rating, student.scholarship
    group_member_query = [gm.pk async for gm in GroupMember.objects.filter(group_id=group_id)]
    rating_list = [student.rating async for student in
                   Student.objects.filter(group_member_id__in=group_member_query).order_by('-rating')]
    scholarship_list = [student.scholarship async for student in
                        Student.objects.filter(group_member_id__in=group_member_query).order_by('-scholarship')]
    print(Student.objects.filter(group_member_id__in=group_member_query).query)
    print(rating_list, scholarship_list)
    rating_place = rating_list.index(rating) + 1
    scholarship_place = scholarship_list.index(scholarship) + 1
    return f"Ваше место по рейтингу: {rating_place}\nВаше место по стипендии: {scholarship_place}"


async def print_top_ratings(group_id: int):
    group_member_query = [gm.pk async for gm in GroupMember.objects.filter(group_id=group_id)]
    rating_list = [(student.rating, student.group_member__user.full_name) async for student in
                   Student.objects.select_related("group_member__user")
                   .filter(group_member_id__in=group_member_query).order_by('-rating')]
    res_string = "Топ-10 игроков по рейтингу:\n_______________\n"
    for index, rating, name in enumerate(rating_list):
        res_string += f"{index + 1}. {name} --- {rating}\n"
    return res_string


async def print_top_scholarships(group_id: int):
    group_member_query = [gm.pk async for gm in GroupMember.objects.filter(group_id=group_id)]
    scholarship_list = [(student.scholarship, student.group_member__user.full_name) async for student in
                        Student.objects.select_related("group_member__user")
                        .filter(group_member_id__in=group_member_query).order_by('-scholarship')]
    res_string = "Топ-10 игроков по стипендии:\n_______________\n"
    for index, scholarship, name in enumerate(scholarship_list):
        res_string += f"{index + 1}. {name} --- {scholarship}\n"
    return res_string
