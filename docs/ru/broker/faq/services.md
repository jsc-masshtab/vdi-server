# Службы системы

Ниже представлен перечень основных сервисов, необходимых для корректной работы брокера, и базовые команды для 
проверки/запуска/остановки. Все команды выполняются либо через `sudo`, либо от привилегированного пользователя.

## Apache2

!!! info "Внимание"
    В ситуации, когда не открывается Web-интерфейс панели администратора, данная служба является первой, с которой 
    следует начать проверку ее активности.

| Тип        | Команда
|------------|---------------------------------------|
| статус     | systemctl status apache2              |
| остановка  | systemctl stop apache2                |
| запуск     | systemctl start apache2               |



## Службы брокера

### Веб-приложение

Веб приложение обрабатывает запросы по протоколу http и соединения по протоколу websockets. 
Его клиентами являются VeiL Connect и веб интерфейс администратора VDI. Возможен запуск нескольких 
эксземляров для увеличения числа обрабатываемых запросов. 

| Тип        | Команда
|------------|---------------------------------------|
| статус     | systemctl status vdi-web              |
| остановка  | systemctl stop vdi-web                |
| запуск     | systemctl start vdi-web               |


### Служба пулов

Процесс, выполнящий задачи, полученные от веб приложения. Задачи поступают из очереди задачи и выполняются 
паралельно. Описание задач, выполняемых службой, можно посмотреть [здесь](../worker/tasks.md).


| Тип        | Команда
|------------|---------------------------------------|
| статус     | systemctl status vdi-pool_worker      |
| остановка  | systemctl stop vdi-pool_worker        |
| запуск     | systemctl start vdi-pool_worker       |


### Монитор состояния компонентов

Процесс мониторит состояние добавленных в VDI брокер контроллеров. 
Осуществляет прием информационных сообщений от контроллеров об изменении статусов и параметров виртуальных
машин.
Деактивирует записи о завершенных соединениях между VDI брокером и тонкими клиентами, если они
по какой-либо причине не были деактивированы штатно (например, при аварийном завершении VeiL Connect).

| Тип        | Команда
|------------|---------------------------------------|
| статус     | systemctl status vdi-monitor_worker      |
| остановка  | systemctl stop vdi-monitor_worker        |
| запуск     | systemctl start vdi-monitor_worker       |


### Менеджер виртуальных машин

Процесс выполняет действия над ВМ, заданные настройками брокера (
удержание ВМ включенными, выключение ВМ при закрытия соединения пользователем и т. п.)
).

| Тип        | Команда
|------------|---------------------------------------|
| статус     | systemctl status vdi-vm_manager      |
| остановка  | systemctl stop vdi-vm_manager        |
| запуск     | systemctl start vdi-vm_manager       |


## Postgresql

База данных, содержащая записи о текущих пользователях, пулах, виртуальных машинах и т.д.

| Тип        | Команда
|------------|---------------------------------------|
| статус     | systemctl status postgresql           |
| остановка  | systemctl stop postgresql             |
| запуск     | systemctl start postgresql            |


## Redis

Резидентная база данных, используемая главным образом в качестве брокера сообщений.
Обеспечивает взаимодействие между службами системы через следующие структуры данных:

 - Очередь задач. Задачи добавляются в очередь со стороны веб приложения и забираются
на исполнение службой пулов.
 - Очередь команд службе пулов от веб приложения (например, команда на отмену задачи).
 - Канал для передачи текстовых сообщений между администраторами и тонкими клиентами.
 - Канал для команд тонким клиентам от администратора.
 - Канал для внутренних сообщений VDI брокера.

| Тип        | Команда
|------------|---------------------------------------|
| статус     | systemctl status redis-server         |
| остановка  | systemctl stop redis-server           |
| запуск     | systemctl start redis-server          |


# Блок схема

!!! example ""
    ![image](../../_assets/vdi/veil_vdi_services.svg)