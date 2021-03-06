# Проверка целостности программы

Непосредственно перед установкой должна быть проверена контрольная
сумма установочного компакт-диска **VeiL Broker**. Проверка
контрольной суммы осуществляется на ЭВМ с установленной 
ОС **Astra Linux Special Edition** версии **1.6** и выше.

Для проверки контрольной суммы установочного диска необходимо
выполнить следующую последовательность действий:

-   войти в ОС под учетной записью суперпользователя (учетная запись
    **root**) и дождаться приглашения ввода консоли;

-   вставить компакт-диск с дистрибутивом **VeiL Broker** в дисковод DVD-ROM;

-   смонтировать компакт-диск с помощью команды   
`mount /media/cdrom`;

-   перейти в каталог точки монтирования компакт-диска (каталог с
    содержимым компакт-диска) с помощью команды  
    `cd /media/cdrom`.

!!! note "Примечание"
    Каталог точки монтирования компакт-диска зависит от настроек
    рабочего места и может отличаться.

-   в командной строке набрать команду для подсчета контрольной суммы

    `find . -type f -exec md5sum {} \; | sort -k2 | md5sum`

!!! note "Примечание"
    Будьте внимательны при наборе команды.

-   дождаться окончания выполнения введенной команды и получить на
    мониторе подсчитанную контрольную сумму;

-   размонтировать компакт-диск с помощью команды  
    `cd /; umount /media/cdrom`;

-   извлечь компакт-диск из дисковода DVD-ROM.

Программа считается готовой к установке, если контрольная сумма,
отображенная на мониторе ЭВМ для установочного компакт-диска,
совпала с контрольной суммой этого диска, записанной в формуляре.

!!! warning "Предупреждение"
    При несовпадении контрольных сумм запрещается производить
    дальнейшие действия по установке программы.
