<div align="center">

<picture>
  <source media="(max-width: 600px)" srcset="./assets/header-mobile.svg" />
  <img src="./assets/header.svg" width="100%" alt="Rezeks — web, mobile, backend. Interfaces. APIs. Experiments." />
</picture>

<br />

<p><a href="#playground"><b>3D-активность</b></a> &nbsp; / &nbsp; <a href="#projects"><b>Проекты</b></a> &nbsp; / &nbsp; <a href="#stack"><b>Технологии</b></a> &nbsp; / &nbsp; <a href="#activity"><b>Статистика</b></a></p>

<br />

### Привет, я Rezeks.

<p>Разрабатываю веб- и мобильные приложения, пишу backend.<br />Здесь — мои проекты на <strong>TypeScript</strong>, <strong>Java</strong>, <strong>Python</strong> и <strong>Go</strong>.</p>

</div>

<br />

<a id="playground"></a>

## 01 &nbsp; / &nbsp; Код в движении

Мой календарь GitHub в объёме. Каждый столбик — один день; высота показывает количество вкладов.

<a href="./assets/activity-3d.svg">
  <picture>
    <source media="(max-width: 600px)" srcset="./assets/activity-3d-mobile.svg" />
    <img src="./assets/activity-3d.svg" width="100%" alt="Трёхмерный календарь активности Rezeks: высота каждого столбика соответствует числу вкладов за день." />
  </picture>
</a>

<details>
<summary><b>📈 Показать динамику по месяцам</b></summary>

<br />

<picture>
  <source media="(max-width: 600px)" srcset="./assets/activity-monthly-mobile.svg" />
  <img src="./assets/activity-monthly.svg" width="100%" alt="Помесячное количество вкладов Rezeks за период календаря GitHub. Первый и последний месяцы могут быть неполными." />
</picture>

</details>

### 🐍 &nbsp; Contribution snake

Змейка проходит по моему календарю и собирает клетки активности.

<img src="./assets/contribution-snake.svg" width="100%" alt="Анимация змейки, которая проходит по календарю вкладов Rezeks и съедает клетки активности." />

<details>
<summary><b>Как читать графики и откуда данные</b></summary>

- Графики используют календарь, доступный в [моём публичном профиле](https://github.com/Rezeks).
- **Вклад** — единица активности GitHub; это не только коммиты.
- 3D-календарь, помесячный график и змейка строятся из одного снимка данных. Период указан на графиках.
- Анимации повторяются при просмотре. Данные обновляются ежедневно через GitHub Actions.

[Открыть 3D-график отдельно](./assets/activity-3d.svg) · [Данные календаря](./assets/activity.json) · [История обновлений](https://github.com/Rezeks/Rezeks/actions/workflows/profile-stats.yml)

</details>

<br />

<a id="projects"></a>

## 02 &nbsp; / &nbsp; Избранные проекты

От интерфейса до серверной логики. Нажми **«Что внутри»**, чтобы заглянуть в проект.

<table>
<tr>
<td width="50%" valign="top">

### 🍕 &nbsp; [next-pizza ↗](https://github.com/Rezeks/next-pizza)

Веб-приложение пиццерии: от каталога до оформления заказа.

`TypeScript` `Next.js` `React` `Prisma`

<details>
<summary><b>Что внутри</b></summary>

- Каталог, корзина и оформление заказов.
- Панель управления и авторизация.
- PostgreSQL, Zustand и Tailwind CSS.

[Открыть исходники →](https://github.com/Rezeks/next-pizza/tree/main/pizza)

</details>

</td>
<td width="50%" valign="top">

### 💬 &nbsp; [JAVA_session ↗](https://github.com/Rezeks/JAVA_session)

Учебный мессенджер с шифрованием, групповыми чатами и передачей файлов.

`Java 21` `Spring Boot` `PostgreSQL` `Kafka`

<details>
<summary><b>Что внутри</b></summary>

- Личные и групповые чаты.
- Передача файлов и работа с шифрованием.
- Spring Security и запуск через Docker.

[Открыть документацию →](https://github.com/Rezeks/JAVA_session#readme)

</details>

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 📱 &nbsp; [AIU_TS ↗](https://github.com/Rezeks/AIU_TS)

Мобильное приложение для поиска скидок и магазинов.

`TypeScript` `React Native` `Expo`

<details>
<summary><b>Что внутри</b></summary>

- Поиск и фильтрация скидок.
- Карта магазинов и профиль пользователя.
- Мобильные интерфейсы на React Native.

[Открыть приложение в коде →](https://github.com/Rezeks/AIU_TS/tree/main/AIU_TP)

</details>

</td>
<td width="50%" valign="top">

### 🔐 &nbsp; [CryptoLab ↗](https://github.com/Rezeks/Data_encryption)

Учебная лаборатория классических шифров с веб-интерфейсом.

`Python` `FastAPI` `JavaScript`

<details>
<summary><b>Что внутри</b></summary>

- Шифрование и расшифровка текста.
- Эксперименты с классическими алгоритмами.
- Python API и интерфейс на HTML, CSS и JavaScript.

[Посмотреть API →](https://github.com/Rezeks/Data_encryption/blob/main/backend/main.py)

</details>

</td>
</tr>
</table>

<details>
<summary><b>Ещё немного кода: Go и Python</b></summary>

| Репозиторий | Что можно найти |
| :--- | :--- |
| [delivery](https://github.com/Rezeks/delivery) | Go-библиотека для расчёта объёмного веса и стоимости доставки. |
| [Python](https://github.com/Rezeks/Python) | Telegram-боты на aiogram и Jupyter notebooks. |

</details>

<br />

<a id="stack"></a>

## 03 &nbsp; / &nbsp; Технологии в моих проектах

<picture>
  <source media="(max-width: 600px)" srcset="./assets/tech-orbit-mobile.svg" />
  <img src="./assets/tech-orbit.svg" width="100%" alt="Анимированная карта стека Rezeks: TypeScript, React, Next.js, Java, Spring, Python, FastAPI и Go вокруг центра Build Lab." />
</picture>

<details>
<summary><b>Развернуть полный стек по направлениям</b></summary>

| Направление | Стек |
| :--- | :--- |
| **Web** | TypeScript · JavaScript · React · Next.js · Tailwind CSS |
| **Mobile** | React Native · Expo |
| **Backend** | Java · Spring Boot · Python · FastAPI · Go |
| **Данные и инструменты** | PostgreSQL · Prisma · Kafka · Docker · Git |

</details>

<br />

<a id="activity"></a>

## 04 &nbsp; / &nbsp; GitHub в цифрах

<a href="https://github.com/Rezeks?tab=repositories">
  <picture>
    <source media="(max-width: 600px)" srcset="./assets/stats-mobile.svg" />
    <img src="./assets/stats.svg" width="100%" alt="Статистика публичных репозиториев Rezeks: проекты, звёзды, подписчики и основные языки. Дата обновления указана на карточке." />
  </picture>
</a>

<details>
<summary>Как обновляется карточка</summary>

Статистика собирается из публичного GitHub API ежедневно через GitHub Actions. Дата последнего обновления указана на изображении; языки считаются по основному языку каждого публичного проекта, без форков и этого профильного репозитория. Если обновление не удалось, в профиле остаётся последний сохранённый снимок.

[История обновлений](https://github.com/Rezeks/Rezeks/actions/workflows/profile-stats.yml) · [Скрипт генерации](./scripts/update_stats.py)

</details>

<br />

---

<div align="center">

<p><strong>Есть идея или вопрос по проекту?</strong><br />Создай issue в соответствующем репозитории — так обсуждение останется рядом с кодом.</p>

<br />

[Смотреть проекты ↗](https://github.com/Rezeks?tab=repositories) &nbsp; · &nbsp; [К началу ↑](#)

<sub>REZEKS &nbsp; / &nbsp; BUILD · LEARN · REPEAT</sub>

</div>
