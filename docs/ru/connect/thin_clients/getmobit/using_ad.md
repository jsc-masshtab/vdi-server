# Использование AD совместно с GM {#using-ad}

!!! tip "Совет"
    В целях упрощения процессов, связанных с управлением учётными записями пользователей, рекомендуется использовать одну и ту же службу каталогов AD для синхронизации с VeiL Broker и с GM Server.

## GM Smart System {#gm_ad}

Более подробно о настройке синхронизации данных с корпоративной службой каталогов можно прочесть в ["Руководстве Администратора"](https://lk.getmobit.ru/cabinet-user/download-doc/49).

1. В веб-панели управления GM Server используя **Настройки** – **Синхронизация с AD** заполнить следующие поля:

    - **AD Сервер** : IP-адрес сервера AD

    - **AD Порт** : порт для подключения к серверу AD (по умолчанию 389)

    - **Логин** : имя пользователя AD

    - **Пароль** : пароль пользователя AD

1. После ввода данных нажать кнопку проверить.

1. Обновить страницу браузера и убедиться, что **Статус** изменился на **Синхронизация запущена**.

## VeiL VDI {#veil_ad}

Настройка работы VeiL Broker со службой каталогов производится [согласно указаниям](../../../broker/operator_guide/ad/).
