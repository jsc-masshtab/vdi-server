# Пример использования RDP-подключений к пулам ВРС

!!! note ""
    Ниже описан сценарий работы с автоматическими пулами ВРС при котором авторизация выполняется на уровне 
    **MS Active Directory**, а подключение пользователей происходит по **RDP**.

### Логически настройку можно разделить на 4 шага:

1. Подготовка [эталонного образа](./example_template_win.md)

1. Добавление [службы каталогов](../../active_directory/ad_extend.md)

1. [Создание](../../active_directory/ad_vm_prepare.md) и [настройка владения](../../auth_v3/groups.md) автоматического пула

1. [Настройка тонкого клиента](../../../connect/settings/rdp_settings.md)

### Функции службы каталогов

- [Авторизация](../../auth_v3/info.md)

!!! note "Примечание"
    Для подключения по **RDP** учетная запись на тонком клиенте должна совпадать с учетной записью внутри ВМ, 
    поэтому стоит использовать **Подготовку ВМ** и **Внешнюю службу авторизации**

- [Первичная синхронизация групп/пользователей](../../active_directory/ad_extend.md)

- [Подготовка ВМ](../../active_directory/ad_vm_prepare.md)