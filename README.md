# SupportHub

Mijozlar murojaatlarini (ticket) boshqarish tizimi. Mijozlar murojaat yuboradi, operatorlar ularni ko'rib chiqadi, admin esa butun tizimni boshqaradi.

**Texnologiyalar:** Django, Django REST Framework, PostgreSQL, JWT (Simple JWT), Redis, Celery + Celery Beat, Django Channels (WebSocket), django-filter, drf-spectacular (Swagger), pytest.

## Loyiha tuzilishi

| Papka | Vazifasi |
|-------|----------|
| `users` | User modeli, ro'yxatdan o'tish, login, profil |
| `tickets` | Category, Ticket, TicketHistory, filter, statistika (cache), Celery tasklar |
| `chat` | Message modeli, WebSocket consumer, xabarlar tarixi |
| `common` | Permission klasslari, pagination, middleware |
| `tests` | Avtomatik testlar |

## Ishga tushirish

### 1-usul. Docker orqali (hammasi birga)

```bash
cp .env.example .env
docker compose up --build
```

Ishga tushadigan xizmatlar: Django server, PostgreSQL, Redis, Celery worker va Celery Beat.
Server: http://localhost:8000

Admin yaratish (boshqa terminalda):

```bash
docker compose exec web python manage.py createsuperuser
```

### 2-usul. Qo'lda (lokal)

1. Virtual muhit yaratib, kutubxonalarni o'rnating (Python 3.10+):

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. PostgreSQL va Redis'ni Docker orqali ishga tushiring:

```bash
cp .env.example .env
docker compose up -d db redis
```

3. Migratsiya va admin:

```bash
python manage.py migrate
python manage.py createsuperuser
```

4. Har bir buyruqni alohida terminalda ishga tushiring:

```bash
python manage.py runserver                 # Django + WebSocket
celery -A supporthub worker -l info        # Celery worker
celery -A supporthub beat -l info          # Celery Beat (davriy vazifalar)
```

## Sozlamalar (.env)

Maxfiy sozlamalar `.env` faylida saqlanadi. Namuna `.env.example` faylida berilgan:
`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_*` (PostgreSQL), `REDIS_HOST`, `REDIS_PORT`, `EMAIL_BACKEND`.

Development rejimida email terminalga chiqadi (`console` backend).

## API hujjati

- Swagger: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- Schema: http://localhost:8000/api/schema/

## Asosiy endpointlar

| Metod | Yo'l | Izoh |
|-------|------|------|
| POST | `/api/auth/register/` | Ro'yxatdan o'tish (rol avtomatik `client`) |
| POST | `/api/auth/login/` | Login, `access` va `refresh` token |
| POST | `/api/auth/token/refresh/` | Tokenni yangilash |
| GET, PATCH | `/api/auth/profile/` | Profil |
| GET, POST | `/api/categories/` | Kategoriyalar (yozish faqat admin) |
| GET, PATCH, DELETE | `/api/categories/{id}/` | Kategoriya |
| GET, POST | `/api/tickets/` | Murojaatlar ro'yxati / yaratish |
| GET, PATCH, DELETE | `/api/tickets/{id}/` | Murojaat (o'chirish faqat admin) |
| GET | `/api/tickets/statistics/` | Statistika (Redis cache, 5 daqiqa; admin va operator) |
| GET | `/api/tickets/{id}/messages/` | Murojaat xabarlari tarixi |
| POST | `/api/tickets/{id}/messages/read/` | Xabarlarni o'qilgan deb belgilash |

Token so'rovlarda `Authorization: Bearer <access>` header orqali yuboriladi.

### Qidiruv, filter, saralash

```
GET /api/tickets/?search=internet
GET /api/tickets/?status=new&priority=urgent
GET /api/tickets/?category=2&operator=5
GET /api/tickets/?created_from=2026-08-01&created_to=2026-08-10
GET /api/tickets/?ordering=-created_at          (created_at, updated_at, priority)
GET /api/tickets/?page=2&page_size=10           (page_size eng ko'pi bilan 100)
```

### Rollar

- **client** — faqat o'z murojaatlarini ko'radi va tahrirlaydi, `status` va `operator` maydonlarini o'zgartira olmaydi.
- **operator** — faqat o'ziga biriktirilgan murojaatlarni ko'radi, holat (`status`) va `priority`ni o'zgartira oladi.
- **admin** — hamma narsani ko'radi va boshqaradi, operator biriktiradi.

Operator yaratish: Django admin panelida (`/admin/`) foydalanuvchi yarating va `role` maydoniga `operator` tanlang.

## WebSocket

Manzil: `ws://localhost:8000/ws/tickets/{ticket_id}/?token=<access_token>`

Token query orqali yoki `Authorization: Bearer <access>` header orqali yuboriladi (Postman'da ikkalasi ham ishlaydi).
Faqat murojaat egasi, biriktirilgan operator va admin ulana oladi.

Yuborish:

```json
{"message": "Muammo hali ham hal bo'lmadi."}
```

Ticketga ulangan hamma qabul qiladi:

```json
{
  "id": 27,
  "ticket_id": 5,
  "sender": "ali",
  "message": "Muammo hali ham hal bo'lmadi.",
  "created_at": "2026-08-10T10:30:00Z"
}
```

## Celery vazifalari

- `notify_urgent_ticket` — yangi `urgent` murojaat yaratilganda operatorga (yoki operator yo'q bo'lsa adminlarga) email yuboradi. Murojaat yaratish so'rovi email yuborilishini kutmaydi.
- `report_stale_new_tickets` — har kuni soat 09:00 da 24 soatdan ortiq `new` holatida turgan murojaatlarni topib, logga yozadi (Celery Beat).

## Loglar

Har bir API so'rovi logga yoziladi:

```
User=15 | Method=GET | Path=/api/tickets/ | IP=127.0.0.1 | Status=200 | Duration=0.084s | Time=2026-08-10 10:30:00
```

Har bir javobda `X-Response-Time` header qaytadi. `/admin/` va `/static/` yo'llari log qilinmaydi.

## Testlar

Testlar PostgreSQL va Redis'siz ishlaydi (test sozlamalarida SQLite va xotiradagi cache ishlatiladi):

```bash
pytest
```
