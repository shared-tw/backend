# shared-tw backend repo

This repository contains backend codes.

## 開發環境
* Python 3.7+
* Django + django-jinja
* Docker

```bash
make dev-dev
```

## 本地測試

```bash
make local-db
python manage.py migrate
python manage.py runserver
```

## HTTP 狀態碼
* `400`: POST 資料有錯誤
* `401`: 未登入
* `403`: 未驗證 EMail
* `422`: 無法更新項目狀態
