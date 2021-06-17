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

### Web-интерфейс брокера

| Тип        | Команда
|------------|---------------------------------------|
| статус     | systemctl status vdi-web              |
| остановка  | systemctl stop vdi-web                |
| запуск     | systemctl start vdi-web               |


### Служба пулов
Описание задач, выполняемых службой, можно посмотреть [здесь](../worker/tasks.md).


| Тип        | Команда
|------------|---------------------------------------|
| статус     | systemctl status vdi-pool_worker      |
| остановка  | systemctl stop vdi-pool_worker        |
| запуск     | systemctl start vdi-pool_worker       |


### Обработчик WSS-соединений

| Тип        | Команда
|------------|---------------------------------------|
| статус     | systemctl status vdi-ws_listener      |
| остановка  | systemctl stop vdi-ws_listener        |
| запуск     | systemctl start vdi-ws_listener       |


## Postgresql

| Тип        | Команда
|------------|---------------------------------------|
| статус     | systemctl status postgresql           |
| остановка  | systemctl stop postgresql             |
| запуск     | systemctl start postgresql            |


## Redis

| Тип        | Команда
|------------|---------------------------------------|
| статус     | systemctl status redis-server         |
| остановка  | systemctl stop redis-server           |
| запуск     | systemctl start redis-server          |
