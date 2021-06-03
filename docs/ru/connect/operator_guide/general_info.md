# Назначение программы

VeiL Connect предназначен для удаленного подключения к виртуальным рабочим столам (ВРС) 
на базе ОС семейства Windows(по протоколам Spice и RDP) и Linux(по протоколу Spice).

!!! note "ОС на базе ядра Linux"
    - Astra Linux Special Edition *Смоленск* версия 1.6 и выше
    - Astra Linux Common Edition *Орел* версия 1.6 и выше
    - Debian 9 и выше
    - Ubuntu 18.04 LTS и выше
    - Centos 7 и выше
    - Astra Linux Common Edition *Орел* в режиме киоска

!!! note "ОС Windows"
    - Windows 7
    - Windows 8.1
    - Windows 10
    - Windows Server 2008 R2
    - Windows Server 2012
    - Windows Server 2012 R2
    - Windows Server 2016
    - Windows Server 2019

VeiL Connect обеспечивает:

- воспроизведение видео в разрешении до FullHD в Web-браузере и в
отдельном приложении-плеере при удаленном подключении к ВРС;

- воспроизведение gif- и flash-анимации без замирания картинки в Web-браузере или приложении для 
просмотра gif- и flash-анимации при удаленном подключении к ВРС;

- комфортную работу САПР Autocad при работе с 3D-графикой при удаленном подключении к ВРС;

!!! note "Примечание"
    Выполняется только с предварительной подготовкой виртуальной машины (ВМ) на ECP VeiL, 
    включающей подключение к ВМ виртуальной видеокарты nVidia с поддержкой технологии GRID, 
    установку драйверов виртуальной видеокарты, подключение лицензии виртуальной видеокарты и 
    установку приложения Spice-tools при подключении по протоколу Spice
    [пример](../../broker/faq/vm/nvidia.md).

- воспроизведение звука без прерываний при подключении к ВРС;

- интеграцию со службой каталогов для хранения учетных записей и данных пользователей (*LDAP* или *AD*);

- прохождение процедуры авторизации и аутентификации с использованием локальных учетных записей
пользователей VeiL Broker;

- прохождение процедуры авторизации и аутентификации на тонком клиенте с использованием учетных
записей пользователей на удаленном контролере LDAP (AD);
  
- подключение к ВРС следующих устройств:
    - манипулятор типа *мышь* через интерфейс USB;
    - клавиатура через интерфейс USB;
    - накопитель flash через интерфейс USB;
    - накопитель на жестком диске через интерфейс USB;
    - наушники через интерфейс TRS 3,5 mm;
    - динамики через интерфейс TRS 3,5 mm;
    - микрофон через интерфейс TRS 3,5 mm;
    - Web-камера через интерфейс USB.

!!! note "Примечание"
    При наличии соответствующих разъёмов в аппаратной платформе.