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


async def change_rating(user_id: int, group_id: int, thread_id: int):
    student_group, group_created = await StudentGroup.objects.aget_or_create(group_id=group_id)
    if group_created:
        student_group.thread_id = thread_id
        now_time = timezone.now() + timedelta(minutes=1)
        first_crontab, _ = await CrontabSchedule.objects.aget_or_create(day_of_week=timezone.now().strftime('%A').lower(),
                                                                        hour=now_time.hour, minute=now_time.minute)
        await PeriodicTask.objects.aget_or_create(crontab=first_crontab,
                                                  name=f'{group_id} begin',
                                                  task='session_begin',
                                                  args=json.dumps([group_id, thread_id]))
        now_time = now_time + timedelta(minutes=1)
        second_crontab, _ = await CrontabSchedule.objects.aget_or_create(day_of_week=timezone.now().strftime('%A').lower(),
                                                                         hour=now_time.hour, minute=now_time.minute)
        await PeriodicTask.objects.aget_or_create(crontab=second_crontab,
                                                  name=f'{group_id} end',
                                                  task='session_end',
                                                  args=json.dumps([group_id, thread_id]))
        await student_group.asave()
    group_member = await GroupMember.objects.aget(user_id=user_id, groups_id=group_id)
    if student_group.is_session:
        text = await change_scholarship(user_id, group_id)
    else:
        student, is_created = await Student.objects.aget_or_create(group_member_id=group_member.pk)
        if is_created:
            text = f"Ну поживи как-нибудь на 100 рублей в месяц, авось не сдохнешь с голоду. Ваш рейтинг - 0."
        elif already_played(timezone.now(), student.date):
            text = f"Пары сегодня закончились, приходите завтра. Ваш рейтинг равен {student.rating}, стипендия составляет {student.scholarship} р."
        else:
            mu, sigma = 0, DAY_MAX / 3 - 1
            delta = norm_distr(mu, sigma)
            student.rating = round(student.rating + delta, 1)
            await student.asave()
            if delta < 0:
                text = f"Схватил двойку по типовику Дзержа - ЛОХ хаххахахаха.\nВаш рейтинг уменьшился на {delta: .1f} единиц и стал равен {student.rating}\nСтипендия составляет {student.scholarship} р."
            else:
                text = f"Насосал, получается)))))\nВаш рейтинг увеличился на {delta: .1f} единиц и стал равен {student.rating}\nСтипендия составляет {student.scholarship} р."
    return text


def normalize(value: float, _min: float, _max: float):
    return (value - _min) / (_max - _min)


async def change_scholarship(user_id: int, group_id: int):
    group_member = await GroupMember.objects.aget(user_id=user_id, groups_id=group_id)
    student, is_created = await Student.objects.aget_or_create(group_member_id=group_member.pk)
    if not is_created and already_played(timezone.now(), student.date):
        text = f'Сессия для тебя уже закончилась, иди бухай'
    elif is_created:
        text = f'Молодец, впервые на сессию пришёл в вуз! Твоя стипендия составляет {student.scholarship} р. Рейтинг равен {student.rating}'
    else:
        rating = student.rating
        prev_rating = student.prev_rating
        delta_rating = rating - prev_rating
        normalized_delta_rating = normalize(delta_rating, -DAY_MAX * 14, DAY_MAX * 14)
        mu = student.scholarship * normalized_delta_rating
        delta = student.scholarship * normalized_delta_rating / 3
        delta_scholarship = norm_distr(mu, delta)
        if delta_rating <= 0:
            student.scholarship = student.scholarship - delta_scholarship
            text = f"Схлопотал двоек на сессии, теперь страдай без стипендии! Она стала равной {student.scholarship} р. Рейтинг обнулён"
        else:
            student.scholarship = student.scholarship + delta_scholarship
            text = f"Всем преподавателям угодил, стипендия увеличилась! Она стала равной {student.scholarship} р. Рейтинг обнулён"
        student.scholarship = round(student.scholarship, 1)
        student.rating = 0
        await student.asave()
    return text


async def print_places(user_id: int, group_id: int):
    group_member = await GroupMember.objects.aget(user_id=user_id, groups_id=group_id)
    student, _ = await Student.objects.aget_or_create(group_member_id=group_member.pk)
    group_member_query = [gm.pk async for gm in GroupMember.objects.filter(groups_id=group_id)]
    rating_list = [student.pk async for student in
                   Student.objects.filter(group_member_id__in=group_member_query).order_by('-rating')]
    scholarship_list = [student.pk async for student in
                        Student.objects.filter(group_member_id__in=group_member_query).order_by('-scholarship')]
    rating_place = rating_list.index(student.pk) + 1
    scholarship_place = scholarship_list.index(student.pk) + 1
    return f"Ваше место по рейтингу: {rating_place}\nВаше место по стипендии: {scholarship_place}"


async def print_top_ratings(group_id: int):
    group_member_query = [gm.pk async for gm in GroupMember.objects.filter(groups_id=group_id)]
    rating_list = [(student.rating, student.group_member.user.full_name) async for student in
                   Student.objects.select_related("group_member__user")
                   .filter(group_member_id__in=group_member_query).order_by('-rating')]
    res_string = "Топ-10 игроков по рейтингу:\n_______________\n"
    for index, (rating, name) in enumerate(rating_list):
        res_string += f"{index + 1}. {name} --- {rating}\n"
    return res_string


async def print_top_scholarships(group_id: int):
    group_member_query = [gm.pk async for gm in GroupMember.objects.filter(groups_id=group_id)]
    scholarship_list = [(student.scholarship, student.group_member.user.full_name) async for student in
                        Student.objects.select_related("group_member__user")
                        .filter(group_member_id__in=group_member_query).order_by('-scholarship')]
    res_string = "Топ-10 игроков по стипендии:\n_______________\n"
    for index, (scholarship, name) in enumerate(scholarship_list):
        res_string += f"{index + 1}. {name} --- {scholarship}\n"
    return res_string
