# Подготовка к установке VeiL Broker

## Характеристики сервера/ВМ

**CPU** / **CPU PRIORITY** - 4 / HIGH

**RAM** / **VDISK** - 4 / 40 GB

!!! note "Проблемы с мышкой с подключением по SPICE"
    Если после установки в ВМ возникают проблемы с "мышкой": 
        1. Воспользуйтесь вкладкой **noVNC**.
        2. Обновите **spice-vdagent** до более актуальной версии (**spice-vdagent_0.18.0-1_amd64**).
        3. Если не помог пункт 2: выключите ВМ, смените графический адаптер на **qxl**,
       добавьте новый USB2.0 контроллер **ehci**, удалите базовый USB3.0 контроллер **nec xhci** 
       и включите ВМ.

## Установка системы 

1. Процесс установки ОС 
   **Astra Linux Special Edition** версии **1.7** релиз **Смоленск** приведен в [приложении](../engineer_guide/application1-7.md).

1. Выбирая имя учётной записи администратора нужно иметь в виду, что имя **vdiadmin** будет в дальнейшем 
   использовано брокером, поэтому необходимо выбрать другое имя, например, **astravdi**.

1. Выбирая компоненты системы обязательно должны быть выбраны **Базовые средства** и 
   **Средства удаленного доступа SSH**, желательно выбрать **Рабочий стол Fly**.
   
    !!! warning "Предупреждение"
        Обратите внимание, что некорректный выбор **Дополнительных настроек ОС** может привести
        к блокировке установки брокера, либо к затруднениям в его работе. Выбирайте данные пункты
        меню, подразумевайте дальнейшую настройку системы.

1. После завершения установки выполните настройку ОС в соответствии с 
   [руководством системного программиста](../engineer_guide/install/prepare/install_os.md). 
   
