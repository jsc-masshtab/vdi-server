# Пользователи

**Пользователи** это наименьшая сущность владения объектами. Обычно закрепление объекта за конкретным пользователем
означает персональную его принадлежность, например, ВМ.

!!! warning "Администратор"
    Пользователи с атрибутом **Администратор** имеют доступ ко всем объектам системы.

## Добавление пользователя

!!! note ""
    Пользователь может быть создан с помощью синхронизации. Описание находится в 
    [соответствующем разделе](../active_directory/ad_extend.md).

Добавление пользователя производится с помощью кнопки **Добавить пользователя** в разделе **Настройки -> Пользователи**.
В открывшемся окне необходимо заполнить следующие поля:
- Имя пользователя
- Пароль
- Почтовый адрес
- Имя
- Фамилия
- Администратор

!!! warning "атрибут Администратор"
    Используйте переключатель с осторожностью. Лучшим выбором будет создать [Группу](./groups.md) с определенным 
    набором [Ролей](./roles.md), чем давать доступ ко всем объектам системы.

!!! example "Пример формы создания"
    ![image](../../../_assets/vdi/auth/create_user.png)

## Информация о пользователе

В информации пользователя доступна следующая информация:
- Дата создания пользователя
- Дата изменения атрибутов пользователя
- Дата последней успешной авторизации пользователя
- Статус пользователя

!!! info "Статус пользователя"
    Пользователи в статусе отличном от **Активный** не имеют возможности входа в систему.

Чтобы закрепить [Роль](./roles.md) за пользователем необходимо нажать кнопку **Добавить роль** в разделе **Роли**
ранее созданного пользователя.

!!! example "Пример закрепления роли за пользователем"
    ![image](../../../_assets/vdi/auth/user_role.png)

!!! note ""
    Пользователь может быть включен в группу в результате синхронизации со службой каталогов. Подробности описаны в 
    [соответствующем разделе](../active_directory/info.md)

Закрепление [Роли](./roles.md) за **Группой** производится аналогично, в разделе **Роли**


## Владение объектами

Чтобы закрепить конкретный объект в системе за **пользователем** необходимо перейти в информацию об объекте и в разделе 
**Пользователи** нажать кнопку **Добавить пользователя**.

!!! example "Пример закрепления пула за пользователем"
    ![image](../../../_assets/vdi/auth/pool_user.png)

!!! info "Владение ВМ"
    Т.к. при выдаче свободной ВМ из пула она закрепляется за конкретным пользователем, то ВМ может содержать 
    персональную информацию пользователя. Для предотвращения случайной выдачи - единственным способом
    переназначения ВМ другому пользователю будет назначение через интерфейс администратора ВМ.