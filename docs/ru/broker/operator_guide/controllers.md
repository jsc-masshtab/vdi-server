# Контроллеры

Контроллер – это узел управления средой ECP VeiL. VeiL Broker взаимодействует с контроллером 
ECP VeiL посредством API для выполнения следующих операций: 

- клонирование, запуск и остановка ВМ;
- получение параметров ВМ для подключения клиентов к ВРМ.

При выборе раздела **Контроллеры** в рабочей области окна интерфейса открывается вкладка **Контроллеры**, 
содержащая список подключенных контроллеров ECP VeiL, включая их имена, IP-адреса, описание и статусы. 
В окне управления доступны следующие операции:

- обновление информации;
- добавление контроллера.

Для добавления связи с новым контроллером Veil необходимо нажать кнопку **Добавить контроллер** 
и в открывшемся диалоговом окне заполнить:

- IP-адрес;
- название;
- токен;
- описание.

После заполнения всех полей необходимо подтвердить операцию, нажав кнопку **Добавить**. 
Название и параметры вновь созданного контроллера появятся в списке имеющихся контроллеров.

!!! note "Примечания"
    1. Пользователь, с которым VeiL Broker подключается к контроллеру ECP VeiL, должен 
    иметь роль *ADMINISTRATOR* и не должен использоваться для авторизации через Web-интерфейс в ECP VeiL. 
    Если данный пользователь не является локальным в ECP VeiL необходимо отметить, что 
    учетные данные пользователя проверяются по протоколу LDAP. 
    2. Авторизация пользователя в ECP VeiL осуществляется посредством *Ключа интеграции*, 
    который генерируется в свойствах пользователя в ECP VeiL и вносится в поле *Токен*. 
    Создание ключа интеграции выполняется в соответствии с руководством оператора ECP VeiL.

Для изменения или просмотра данных о контроллере необходимо выбрать имя контроллера, 
после чего в рабочей области отобразится имя выбранного контроллера и информация по нему, 
разграниченная по следующим вкладкам:

1. **Информация** – содержит сведения о контроллере:
 
   - название (редактируемый параметр);
   - описание (редактируемый параметр);
   - IP-адрес (редактируемый параметр);
   - токен;
   - версия;
   - статус.

2. **Кластеры** – содержит список всех кластеров на выбранном контроллере, включая их названия, 
количество серверов, сведения о CPU, сведения о RAM и статусы.
Более подробное описание кластеров приведено в [кластерах](clusters.md).

3. **Пулы ресурсов** – содержит список всех пулов ресурсов на выбранном контроллере, 
включая их названия, количество ВМ, ограничения по памяти и CPU.
Более подробное описание пулов ресурсов приведено в [пулах ресурсов](resource_pools.md).

4. **Серверы** – содержит список всех серверов на выбранном контроллере, 
включая их названия, IP-адреса, сведения о CPU, сведения о RAM и статусы.
Более подробное описание серверов приведено в [серверах](nodes.md).

5. **Пулы данных** – содержит список всех пулов данных на выбранном контроллере, 
включая их названия, типы, размер свободной и занятой памяти, статусы.
Более подробное описание пулов данных приведено в [пулах данных](nodes.md).

6. **Шаблоны ВМ** – содержит список шаблонов ВМ, размещенных на 
выбранном контроллере, включая их названия и статусы.
Более подробное описание шаблонов ВМ приведено в [шаблонах](templates.md).

7. **Виртуальные машины** – содержит список всех ВМ, размещенных на выбранном 
контроллере, включая их названия, пулы и статусы.
Более подробное описание ВМ приведено в [виртуальных машинах](domains.md).

В окне управления контроллером доступны следующие операции:

- удаление контроллера. При нажатии на кнопку **Удалить контроллер** в открывшемся 
диалоговом окне необходимо подтвердить операцию, нажав кнопку **Удалить**;
- проверка соединения. При нажатии на кнопку **Проверка соединения** осуществляется 
автоматическая проверка соединения с контроллером;
- включение сервисного режима. Включенный сервисный режим деактивирует контроллер, 
все операции с контроллером становятся неактивными.