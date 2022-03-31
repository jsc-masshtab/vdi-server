# Пулы приложений

Пул приложений - это интеграция RDS (Remote Desktop Services) с **VeiL Broker** (**VeiL VDI**).

Пул содержит одну общую для всех пользователей машину, на которой установлена роль **брокер подключений RDS** 
(Remote Desktop Connection Broker).

При подключении к пулу пользователю будет показан список доступных приложений для запуска ([инструкция по созданию коллекции приложений](https://docs.microsoft.com/ru-ru/windows-server/remote/remote-desktop-services/rds-create-collection)).

После выбора приложения оно будет доставлено пользователю.

## Создание пула приложений

1. Разверните **Remote Desktop Services** на виртуальных машинах **ECP VeiL**.
1. На машине с ролью **Connection Broker** выполните действия согласно README.txt (https://veil-update.mashtab.org/veil_agent/iso/windows/rds/README.txt)
1. В Web-интерфейсе **VeiL Broker** перейдите на вкладку **Пулы** и нажмите кнопку **Добавить пул**.
1. Выберите создание RDS пула и нажмите **Далее**.
1. Задайте параметры пула и выберите машину, на которой установлена роль **Remote Desktop Connection Broker**.
1. Нажмите кнопку **Создать**.

!!! note "Примечание"
    Для интеграции пользователей необходимо добавить в **VeiL Broker** службу каталогов, используемую в RDS. 
    [Добавление службы каталогов](../active_directory/ad_extend.md).
    
!!! note "Примечание"
    QEMU Guest Agent на машине с ролью Remote Desktop Connection Broker должен запускаться с
    учетными данными администратора AD [Настройка qemu-guest-agent](../../broker/vm/guest_agent.md).