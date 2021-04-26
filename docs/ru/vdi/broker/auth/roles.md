# Роли

**Роли** это набор предустановленных сущностей, которые не подлежат редактированию.
Основное назначение сущности это доступ к разделам панели администратора, однако, они могут быть использованы и как
атрибут владения сущностями в системе.

!!! warning "Внимание"
    Пользователю с атрибутом **Администратор** не нужно обладать конкретной ролью, чтобы иметь доступ к ее объектам.

Ниже перечислены существующие роли:
- SECURITY_ADMINISTRATOR
- OPERATOR
- ADMINISTRATOR

Чтобы закрепить конкретный объект в системе за **ролью** необходимо перейти в информацию об объекте и в разделе 
**Роли** нажать кнопку **Добавить роль**.

!!! example "Пример закрепления пула за ролью"
    ![image](../../../_assets/vdi/auth/pool_role.png)

## SECURITY_ADMINISTRATOR

Наличие роли является обязательной для доступа к разделам панели администратора:
- Службы каталогов
- Группы
- Пользователи

## OPERATOR

Наличие роли является обязательной для доступа к разделам панели администратора:
- Журнал

## ADMINISTRATOR

Самая большая роль, нужна для доступа ко всем остальным разделам панели администратора.

<hr/>