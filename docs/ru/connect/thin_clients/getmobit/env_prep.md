# Подготовка окружения {#env-prep}

## Инфраструктура VeiL {#veil-env}

Для начала использования системы на базе решения **GM-Box** из линейки продуктов **GM Smart System** необходимо подготовить следующее:

1. Развернуть и настроить облачную платформу **ECP VeiL** согласно [руководству](https://veil.mashtab.org/docs/latest/).

1. Развернуть и настроить брокер подключений **VeiL VDI** – **VeiL Broker** согласно [руководству](https://veil.mashtab.org/vdi-docs/broker/engineer_guide/install/).

## Подготовка виртуальных машин (ВМ) {#virt-machines}

1. Используя подготовленную инфраструктуру VeiL [создать ВМ](https://veil.mashtab.org/docs/latest/base/operator_guide/domains/create/) для установки GM Server. Параметры ВМ должны соответствовать следующим рекомендованным аппаратным требованиям (актуальные данные доступны в документе ["Требования к инфраструктуре"](https://lk.getmobit.ru/cabinet-user/download-doc/40)):

    * Минимум 2 vCPU (ядра процессора)

    * Минимум 16 GB RAM

    * 100 GB HDD

1. На виртуальную машину, выполняющую роль сервера управления следует установить операционную систему Ubuntu 16.04 LTS (64bit) либо иную Linux систему, имеющую менеджер deb пакетов и обладающую поддержкой пакета docker версии не ниже 17.09.0.

1. Для вышеуказанной виртуальной машины необходим статический IP-адрес.

1. Аналогично первому пункту создать необходимое количество ВМ и установить на них операционные системы (ОС), которые планируется использовать в качестве гостевых. Подробнее о подготовке ВМ и установке некоторых ОС читайте в соответствующих разделах руководства, для [Windows](../../../broker/faq/rdp/example_template_win/) и для [Linux](../../../broker/faq/rdp/example_template_lin/).

## Подготовка сети для работы с GM-Box {#network-setup}

Для работы с устройствами GM-Box в сети рекомендуется развернуть или настроить сервер DHCP, предоставляющий подключаемым устройствам следующую информацию:

* IP-адрес подключенного устройства;

* название домена;

* IP-адрес шлюза по умолчанию;

* IP-адрес сервера имён (DNS);

* IP-адрес сервера точного времени (NTP);

* для автоматического поиска сервера управления GM Server необходимо указать локальный домен в DHCP option 119 — 'Domain Search List'.

Также крайне желательно обеспечить наличие A-записи в DNS, связывающей IP-адрес сервера управления GM Server с именем getmobit.example.site

!!! warning "Предупреждение"
    В случае невыполнения вышеуказанных рекомендаций, то есть при отсутствии DNS-записи и настроенного DHCP сервера, устройство GM-Box не сможет автоматически обнаружить и подключиться к серверу управления GM Server. Таким образом, для каждого устройства GM-Box потребуется ручная настройка параметров сети.