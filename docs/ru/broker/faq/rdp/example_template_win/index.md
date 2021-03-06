# Подготовка эталонного образа на основе Windows 8.1/10

## Общие сведения

Эталонный образ ВМ используется для создания шаблона ВМ. 
Шаблон ВМ позволяет существенно сократить время развертывания новых ВМ путем клонирования новых ВМ из шаблона без необходимости создания вручную новой ВМ, установки ОС и дополнительного программного обеспечения (ПО) на ВМ.

Более полную информацию о шаблонах ВМ можно прочитать в [руководстве оператора VeiL Broker](https://veil.mashtab.org/vdi-docs/broker/operator_guide/templates/).

Создание эталонного образа на основе Windows 8.1/10 состоит из следующих шагов:

1. Создание виртуальной машины и установка ОС;
2. Установка драйверов и дополнительного ПО;
3. Оптимизация ОС c помощью **VeiL Guest Utils**;
4. Добавление пользователей в группу удалённых рабочих столов для подключения по RDP к ВМ.

!!! note "Примечание"
    Эталонный образ ВМ не может быть использован как самостоятельная ВМ. Использование эталонных ВМ позволяет сохранять исходный образ ВМ неизменным.