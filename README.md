# PdfCheckMaker

PdfCheckMaker генерирует PDF-чеки из CSV/JSON-данных по HTML-шаблонам Jinja2. Архитектура разделена так, чтобы новые источники данных и интерфейсы добавлялись без переписывания ядра.

## Структура

```text
src/pdfcheckmaker/
  core/              # модели, расчеты, QR, PDF-render, фасад InvoiceGenerator
  datasources/       # Strategy + Registry для CSV/JSON и будущих источников
  templates_engine/  # загрузка template.html и manifest.yaml
  interfaces/cli/    # интерактивное меню questionary
data/                # примеры входных данных
templates/           # HTML-шаблоны с manifest.yaml
tests/               # pytest
output/              # PDF создаются здесь при запуске CLI
```

## Установка

Все команды ниже выполняются из корня проекта. Зависимости устанавливаются через `requirements.txt`, который ставит проект в editable-режиме вместе с dev-зависимостями из `pyproject.toml`.

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
python -m ensurepip --upgrade
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m ensurepip --upgrade
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Если PowerShell блокирует запуск скрипта активации, разрешите его только для текущей сессии:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### GTK/Pango для WeasyPrint на Windows

WeasyPrint на Windows использует нативные библиотеки Pango/Cairo/GLib. По официальной инструкции WeasyPrint 69.0, если WeasyPrint нужен как Python-библиотека, самый простой способ поставить эти DLL — через MSYS2.

1. Установите [MSYS2](https://www.msys2.org/) с настройками по умолчанию. MSYS2 рекомендует короткий ASCII-путь без пробелов; стандартный `C:\msys64` подходит.
2. Откройте установленную оболочку MSYS2 и поставьте Pango с зависимостями:

```bash
pacman -S mingw-w64-x86_64-pango
```

3. Закройте MSYS2, откройте обычный Windows PowerShell, активируйте `venv` проекта и установите Python-зависимости:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

4. Проверьте, что WeasyPrint видит нативные библиотеки:

```powershell
python -m weasyprint --info
```

Если появляется ошибка вида `cannot load library 'libgobject-2.0-0'`, укажите путь к DLL из MSYS2:

```powershell
$env:WEASYPRINT_DLL_DIRECTORIES = "C:\msys64\mingw64\bin"
python -m weasyprint --info
```

Чтобы переменная сохранялась между сессиями PowerShell:

```powershell
[Environment]::SetEnvironmentVariable("WEASYPRINT_DLL_DIRECTORIES", "C:\msys64\mingw64\bin", "User")
```

Источники: [WeasyPrint First Steps / Windows](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows), [WeasyPrint troubleshooting for missing libraries](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#missing-library), [MSYS2 installer docs](https://www.msys2.org/docs/installer/).

## Запуск

Перед запуском активируйте `.venv`, если она еще не активирована.

Linux/macOS:

```bash
source .venv/bin/activate
pdfcheckmaker
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
pdfcheckmaker
```

CLI покажет доступные файлы из `data/`, шаблоны из `templates/`, затем список `invoice_id`. Можно сгенерировать один чек или весь batch. Одиночный PDF после генерации откроется системной программой.

## Формат данных

CSV использует одну строку на позицию чека и группируется по `invoice_id`:

```csv
invoice_id,issue_date,seller_name,buyer_name,item_name,item_quantity,item_price
INV-1,15.06.2024,ООО Ромашка,ИП Иванов,Клавиатура,2,4500.00
```

JSON хранит список чеков:

```json
{
  "invoices": [
    {
      "invoice_id": "INV-1",
      "issue_date": "15.06.2024",
      "seller": { "name": "ООО Ромашка", "inn": "123", "address": "Москва" },
      "buyer": { "name": "ИП Иванов" },
      "items": [{ "name": "Клавиатура", "quantity": 2, "price": 4500.0 }]
    }
  ]
}
```

## Шаблоны

Каждый шаблон лежит в отдельной папке:

```text
templates/invoice_standard/
  manifest.yaml
  template.html
```

`manifest.yaml` описывает имя, описание, обязательные поля, вложенную схему и настройки QR. Перед рендером ядро проверяет, что `Invoice` удовлетворяет манифесту. HTML использует Jinja2: циклы, условия, форматирование и QR-картинку как base64.

## Расширение

Новый источник данных:

1. Создать класс-наследник `DataSource` с методом `load() -> list[Invoice]`.
2. Зарегистрировать расширение в `default_registry()` или в собственном registry интерфейса.
3. Остальной код менять не нужно.

Новый интерфейс вызывает только фасад:

```python
from pdfcheckmaker.core.generator import InvoiceGenerator

InvoiceGenerator().generate_one(invoice, template_dir, output_dir)
```

## Тесты

Перед запуском тестов активируйте `.venv`. В `pyproject.toml` для pytest задана временная папка `output/pytest_tmp` и отключен cache provider, чтобы тесты не зависели от доступа к системному `Temp` и `.pytest_cache`.

Linux/macOS:

```bash
source .venv/bin/activate
python -m pytest
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
python -m pytest
```
