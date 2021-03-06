# Группы

Вкладка **Группы** позволяет организовать пользователей ВРМ в группы с возможностью назначения каждой 
группе пользователей определенных ролей и разрешений.

При выборе подраздела **Группы** (раздел **Настройки** основного меню программы) в рабочей 
области окна интерфейса открывается вкладка **Группы**, содержащая список имеющихся групп, включая 
их названия, описания и количество пользователей в группе. Также доступны следующие операции:

- обновление информации;
- создание новой группы;
- выбор группы с применением фильтра.

Создание новой группы осуществляется с помощью нажатия кнопки **Добавить группу**. В открывшемся 
диалоговом окне необходимо заполнить следующие поля:

- название;
- описание.

После заполнения всех полей необходимо подтвердить операцию, нажав кнопку **Добавить**. Название и 
описание вновь созданной группы появятся в списке имеющихся групп.

Для изменения или просмотра сведений о конкретной группе необходимо нажать на ее название, 
после чего в рабочей области отобразится название выбранной группы и информация по ней, 
разграниченная по типам параметров:

1. **Информация** – содержит сведения о группе:

     -  название (редактируемый параметр);
     -  описание (редактируемый параметр);
     -  количество пользователей в группе;
     -  дата и время создания;
     -  дата и время последнего редактирования.

     С помощью кнопки **Удалить группу** существует возможность удаления текущей группы;

2. **Роли** – содержит перечень доступных ролей для выбранной группы пользователей. В окне доступны следующие 
операции:

     -  обновление информации;
     -  добавления новой роли. При нажатии на кнопку **Добавить роль** открывается окно назначения новой 
    роли для выбранной группы пользователей, в котором с помощью раскрывающегося списка пользователь выбирает 
    одну или несколько ролей для группы и сохраняет изменения с помощью кнопки **Добавить**;
     -  удаление роли. При нажатии на кнопку **Удалить роль** открывается окно удаления роли для группы, в 
    котором с помощью раскрывающегося списка пользователь выбирает роль и подтверждает операцию нажатием кнопки **Удалить**.

     Группе пользователей доступны следующие роли:

     -  ADMINISTRATOR (роль администратора);
     -  SECURITY_ADMINISTRATOR (роль администратора безопасности);
     -  OPERATOR (роль пользователя ВМ).

     Назначаемые роли ограничивают привилегии, предоставляемые пользователю в группе:

     - ADMINISTRATOR имеет полные права на управление ресурсами VeiL Broker;
     - SECURITY_ADMINISTRATOR имеет право на управление пользователями и ролями;
     - OPERATOR – это роль, предоставляемая пользователю *по умолчанию*. Данная роль ограничивает 
       пользователя только возможностью подключения к ВРМ.

3. **Пользователи** – содержит список пользователей, включенных в выбранную группу.
В окне доступны следующие операции:

     - добавление пользователя. При нажатии на кнопку **Добавить пользователя** открывается диалоговое 
    окно добавления пользователей к группе, в котором с помощью раскрывающегося списка существует 
    возможность выбрать одного или несколько пользователей, ранее зарегистрированных в среде VeiL Broker. 
    Для сохранения изменений необходимо нажать кнопку **Добавить**;
     - удаление пользователя. При нажатии на кнопку **Удалить пользователя** открывается диалоговое 
    окно удаления пользователей из группы, в котором с помощью раскрывающегося списка существует 
    возможность выбрать одного или несколько пользователей. Для подтверждения операции необходимо 
    нажать кнопку **Удалить**.

     Для групп, загружаемых из AD, редактирование списка пользователей недоступно;

4. **Разрешения** – содержит перечень доступных разрешений на действия при работе с клиентским 
ПО VeiL Connect для выбранной группы пользователей. 
 
     В окне доступны следующие операции:

     - обновление информации;
     - добавление разрешения. При нажатии на кнопку **Добавить разрешение** открывается окно добавления 
    нового разрешения для выбранной группы пользователей, в котором с помощью раскрывающегося списка 
    пользователь выбирает одно или несколько разрешений для группы и сохраняет изменения с помощью кнопки **Добавить**;
     - отключение разрешения. При нажатии на кнопку **Отключить разрешение** открывается окно отключения 
    разрешения для группы, в котором с помощью раскрывающегося списка пользователь выбирает разрешение 
    и подтверждает операцию нажатием кнопки **Отключить**.

     Группе пользователей доступны следующие разрешения:

     - USB_REDIR (разрешение на перенаправление USB-устройств);
     - FOLDERS_REDIR (разрешение на перенаправление папок);
     - SHARED_CLIPBOARD (разрешение на использование общего буфера обмена).
