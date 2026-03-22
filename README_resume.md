# Resume module (окно резюме) — документация

Этот документ описывает модуль **резюме** в проекте Studlink: страницу конструктора `/resume/`, API автосохранения и публичную страницу `/u/<username>/`.

---

## 1) Состав модуля

Модуль резюме включает 3 части:

1) **Конструктор резюме**: `GET /resume/`
   - редактирование данных резюме;
   - автосохранение через API;
   - live preview (карточка справа).

2) **API автосохранения**: `POST /api/save-resume/`
   - принимает JSON;
   - обновляет модель `Resume`.

3) **Публичная страница резюме**: `GET /u/<username>/`
   - Bootstrap-страница просмотра;
   - поддерживает печать/PDF.

---

## 2) Связанные файлы

### Backend

- `mysite/myapp/models.py`
  - `Resume` — основная сущность резюме.
- `mysite/myapp/views.py`
  - `resume_form` — HTML конструктора.
  - `save_resume` — DRF endpoint для автосохранения.
  - `public_resume` — HTML публичного резюме.
- `mysite/myapp/urls.py`
  - роуты `/resume/`, `/api/save-resume/`, `/u/<username>/`.

### Templates

- `mysite/myapp/templates/resume_form.html` — UI конструктора + JS.
- `mysite/myapp/templates/public_resume.html` — UI публичного резюме + print CSS.

---

## 3) URL’ы

```http
GET  /resume/            # конструктор
POST /api/save-resume/   # автосохранение
GET  /u/<username>/      # публичное резюме
```

---

## 4) Модель данных `Resume`

Файл: `mysite/myapp/models.py` → `class Resume(models.Model)`.

Поля, которые используются конструктором/публичной страницей в текущей версии:

| Поле | Тип | Описание |
|------|-----|----------|
| `user` | OneToOne(User) | владелец резюме |
| `full_name` | CharField | ФИО |
| `position` | CharField | желаемая должность |
| `employment` | CharField | занятость |
| `work_schedule` | CharField | график |
| `salary` | IntegerField(null=True) | зарплата |
| `currency` | CharField | валюта (RUB/USD/EUR) |
| `city` | CharField | город |
| `citizenship` | CharField | гражданство |
| `birth_date` | DateField(null=True) | дата рождения |
| `gender` | CharField | пол |
| `relocation` | CharField | переезд |
| `family_status` | CharField | семейное положение |
| `children` | BooleanField | есть дети |
| `about` | TextField | текст «О себе» |
| `army_service` | BooleanField | служба в армии |
| `medical_book` | BooleanField | мед.книжка |
| `created_at` / `updated_at` | DateTimeField | метаданные |

> В проекте уже есть модели `Skill`, `ResumeSkill`, `Education`, `Experience`, `SocialLink`,
> но их сохранение/отображение пока не подключено (часть UI может быть заглушкой).

---

## 5) Страница конструктора: `/resume/`

### 5.1 Backend: `views.resume_form`

Вьюха:

- проверяет, что пользователь авторизован (иначе redirect на `auth`);
- создаёт резюме, если его ещё нет:

```python
resume, _ = Resume.objects.get_or_create(user=request.user)
```

- рендерит `resume_form.html` и передаёт контекст:

```python
{"resume": resume}
```

### 5.2 Frontend: `resume_form.html`

UI:
- Bootstrap `accordion` (секции «Основная информация», «Личная информация», «О себе», «Дополнительно»);
- правая колонка: карточка превью;
- верхняя панель: бейдж статуса сохранения и кнопки «Посмотреть»/«Печать».

JS:

- `collectData()` — собирает значения полей в объект.
- `updatePreview()` — обновляет превью справа.
- `autoSave()` — отправляет JSON в `/api/save-resume/`.
- `setInterval(autoSave, 3000)` — автосохранение раз в 3 сек.
- `lastPayload` — защита от повторной отправки одинакового payload.

### 5.3 CSRF

Чтобы POST работал с CSRF:

- `resume_form` помечен `@ensure_csrf_cookie`, поэтому при открытии страницы выставляется cookie `csrftoken`.
- JS читает cookie и отправляет заголовок `X-CSRFToken`.
- `fetch` вызывается с `credentials: 'same-origin'`.

---

## 6) API автосохранения: `/api/save-resume/`

Backend: `views.save_resume`.

**Auth:** `IsAuthenticated` (DRF).

### 6.1 Формат входных данных

JSON соответствует объекту из `collectData()`.

Пример:

```json
{
  "full_name": "Иванов Иван",
  "position": "Backend-разработчик",
  "employment": "Полная",
  "work_schedule": "Удаленно",
  "salary": "150000",
  "currency": "RUB",
  "citizenship": "Россия",
  "birth_date": "2000-01-01",
  "gender": "Мужской",
  "city": "Москва",
  "relocation": "Возможен переезд",
  "family_status": "Холост",
  "children": false,
  "about": "Коротко о себе...",
  "army_service": false,
  "medical_book": false
}
```

### 6.2 Правила обработки на сервере

- `salary` приводится к `int` (или `None`, если пусто/некорректно)
- `birth_date` парсится через `parse_date`
- флаги приводятся к `bool`

### 6.3 Ответ

```json
{"status": "saved"}
```

---

## 7) Публичная страница: `/u/<username>/`

Backend: `views.public_resume`.

Template: `public_resume.html`.

### 7.1 Что отображается

- шапка (hero card): имя, должность, город, занятость, график, зарплата;
- бейджи: переезд/дети/армия/мед.книжка;
- «О себе» и «Личная информация».

### 7.2 Печать / PDF

В шаблоне есть `@media print`, который скрывает навбар/футер/кнопки и убирает тени у карточек.

---

## 8) Как расширять (skills/education/experience/social links)

Сейчас навыки в конструкторе — UI-демо. Чтобы сделать полноценное сохранение:

1) Frontend:
   - хранить массив навыков в JS;
   - отправлять `skills: ["Django", "Git", ...]`.

2) Backend:
   - в `save_resume` создавать/находить `Skill`;
   - пересобирать связи `ResumeSkill`.

По аналогии можно добавить массивы `experience`/`education` и обновлять таблицы `Experience` и `Education`.


