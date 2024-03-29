# Пулы ВРС

Пулы виртуальных рабочих столов (ВРС) – логические группы, которые представляют собой организационные единицы (ОЕ), 
предназначенные для группирования ВРС и применения к ним групповых настроек и политик безопасности.
 
При выборе раздела **Пулы** основного меню программы в рабочей области окна интерфейса 
открывается вкладка **Пулы рабочих столов**, содержащая список имеющихся пулов ВРС, 
включая их названия, названия контроллеров, количество доступных ВМ, количество 
пользователей, имеющих доступ к данному пулу, типы и статусы пулов. В окне управления 
пулами становится доступна операция добавления нового пула.

Для добавления нового пула ВРС необходимо нажать кнопку **Добавить пул**, 
после чего откроется окно мастера создания пула ВМ, в котором с помощью кнопки 
навигации **Далее** и **Назад** необходимо пройти все этапы создания пула ВРС 
последовательно заполняя поля информацией.

На первом этапе необходимо выбрать тип пула (*автоматический*, *гостевой*, *статистический* или *RDS*).

На втором этапе для статистического пула необходимо задать:

- имя пула (редактируемый параметр);
- тип подключения (множественный выбор из раскрывающегося списка). 
Может принимать значения: *RDP*, *NATIVE_RDP*, *SPICE*, *SPICE_DIRECT*;
- контроллер (выбор из раскрывающегося списка);
- пул ресурсов (выбор из раскрывающегося списка);
- виртуальные машины (множественный выбор из раскрывающегося списка).

Для пула RDS необходимо задать:

- имя пула (редактируемый параметр);
- тип подключения (множественный выбор из раскрывающегося списка). 
Может принимать значения: *RDP*, *NATIVE_RDP*, *SPICE*, *SPICE_DIRECT*;
- контроллер (выбор из раскрывающегося списка);
- пул ресурсов (выбор из раскрывающегося списка);
- виртуальная машина (выбор из раскрывающегося списка).

Для автоматического пула необходимо задать:

- имя пула;
- тип подключения (множественный выбор из раскрывающегося списка). 
Может принимать значения: *RDP*, *NATIVE_RDP*, *SPICE*, *SPICE_DIRECT*;
- контроллер (выбор из раскрывающегося списка);
- пул ресурсов (выбор из раскрывающегося списка);
- пул данных (выбор из раскрывающегося списка);
- шаблон имени ВМ. Имя шаблона не должно превышать 63 символа и может состоять 
из букв латинского алфавита, цифр и знаков;
- наименование организационной единицы для добавления ВМ в AD. Наименование контейнера для MS Windows Active 
Directory (MS AD), в который необходимо включить созданные ВМ при подготовке;
- начальное количество ВМ (количество ВМ, которые будут созданы вместе с пулом);
- максимальное количество создаваемых ВМ (максимальная количество ВМ пула);
- шаг расширения пула (количество ВМ, которые будут создаваться при расширении пула);
- пороговое количество свободных ВМ (значение, при достижении которого будет запущено автоматическое расширение пула); 
- возможность создания тонких клонов (выставить отметку в чек-боксе). 
Атрибут, используемый при создании ВМ из шаблона;
- возможность подготавливать ВМ (выставить отметки в чек-боксе). 
Атрибуты, указывающие на необходимость запуска процедур, связанных с подготовкой ВМ после их создания.

Для гостевого пула необходимо задать:

- имя пула;
- тип подключения (множественный выбор из раскрывающегося списка). 
Может принимать значения: *RDP*, *NATIVE_RDP*, *SPICE*, *SPICE_DIRECT*;
- контроллер (выбор из раскрывающегося списка);
- пул ресурсов (выбор из раскрывающегося списка);
- пул данных (выбор из раскрывающегося списка);
- шаблон имени ВМ. Имя шаблона не должно превышать 63 символа и может состоять 
из букв латинского алфавита, цифр и знаков;
- начальное количество ВМ (количество ВМ, которые будут созданы вместе с пулом);
- максимальное количество создаваемых ВМ (максимальная количество ВМ пула);
- шаг расширения пула (количество ВМ, которые будут создаваться при расширении пула);
- пороговое количество свободных ВМ (значение, при достижении которого будет запущено автоматическое расширение пула); 
- время жизни ВМ после потери связи в секундах (отметка времени, по истечению которой ВМ будет удалена).

На третьем этапе необходимо проверить заполненную ранее информацию и, если она достоверна, 
нажать на кнопку **Создать пул**. Название и параметры вновь созданного пула появятся в списке 
имеющихся пулов рабочих столов.

Для создания пула необходимо указать типы подключения к ВМ в пуле, которые будут доступны тонкому клиенту. 
[Подробнее о типах подключения](../faq/remote_conn_protocols.md).

!!! note "Примечание" 
    Если в процессе создания пула подготовились не все ВМ или необходимо выполнить подготовку ВМ 
    по изменившимся параметрам, то для продолжения процесса подготовки необходимо перейти в 
    раздел виртуальной машины созданного пула (**Пулы** – **Виртуальные машины** – <название ВМ>) 
    и нажать на кнопку **Подготовить ВМ**. Продолжится подготовка ВМ с последнего успешного действия.

Для изменения или просмотра уже существующего пула необходимо нажать на его название, 
после чего в рабочей области пулов рабочих столов отобразится название выбранного пула и 
информация по нему, разграниченная по следующим вкладкам:

- информация;
- виртуальные машины;
- пользователи;
- группы.

При переходе от одной вкладки к другой в области отображения информации изменяется 
список объектов, относящийся к данной вкладке.

При выборе вкладки **Информация** в рабочей области отображается информация, вид которой 
зависит от выбранного типа пула. Пользователю будет дана возможность просмотреть 
и изменить следующие параметры:

1. для статистического пула:

    - название (редактируемый параметр);
    - тип пула;
    - тип подключения пула (редактируемый параметр);
    - наименование контроллера;
    - IP-адрес контроллера;
    - наименование пула ресурсов;
    - всего ВМ;
    - количество пользователей;
    - действие над ВМ (редактируемый параметр);
    - статус;

2. для автоматического пула:

    - название (редактируемый параметр);
    - тип пула;
    - тип подключения пула (редактируемый параметр);
    - наименование контроллера;
    - IP-адрес контроллера;
    - возможность создания тонких клонов (редактируемый параметр);
    - возможность держать включенными ВМ с пользователями (редактируемый параметр);
    - действие над ВМ (редактируемый параметр);
    - наименование пула ресурсов;
    - наименование пула данных;
    - шаблон ВМ;
    - начальное количество ВМ;
    - шаг расширения пула (редактируемый параметр);
    - максимальное количество создаваемых ВМ (редактируемый параметр);
    - пороговое количество свободных ВМ (редактируемый параметр);
    - количество доступных ВМ;
    - шаблон для имени ВМ (редактируемый параметр);
    - подготовка ВМ (редактируемый параметр), состоящая из возможности включать удаленный доступ на ВМ, включать ВМ, задавать hostname ВМ и вводить ВМ в домен (только для Windows);
    - наименование организационной единицы для добавления ВМ в AD (редактируемый параметр);
    - количество пользователей;
    - статус.

3. для гостевого пула:

    - название (редактируемый параметр);
    - тип пула;
    - тип подключения пула (редактируемый параметр);
    - наименование контроллера;
    - IP-адрес контроллера;
    - создание тонких клонов;
    - возможность держать включенными ВМ с пользователями (редактируемый параметр);
    - время жизни ВМ после потери связи в секундах (редактируемый параметр);
    - наименование пула ресурсов;
    - наименование пула данных;
    - шаблон ВМ;
    - начальное количество ВМ;
    - шаг расширения пула (редактируемый параметр);
    - максимальное количество создаваемых ВМ (редактируемый параметр);
    - пороговое количество свободных ВМ (редактируемый параметр);
    - количество доступных ВМ;
    - шаблон для имени ВМ (редактируемый параметр);
    - подготовка ВМ, состоящая из включения удаленного доступа на ВМ и включения ВМ;
    - количество пользователей;
    - статус.

4. для RDS пула:

    - название (редактируемый параметр);
    - тип пула;
    - тип подключения пула (редактируемый параметр);
    - наименование контроллера;
    - IP-адрес контроллера;
    - наименование пула ресурсов;
    - всего ВМ;
    - количество пользователей;
    - действие над ВМ (редактируемый параметр);
    - статус.

Существует возможность удаления выбранного пула с помощью кнопки **Удалить пул**.

!!! note "Примечание" 
    При удалении пула ВМ в среде ECP VeiL удаляются только тонкие клоны, созданные в VeiL  Broker. 
    Удаления ВРС из MS AD не производится.
    
!!! note "Действие над ВМ" 
    Существует возможность выбрать действие над ВМ и его тайм-аут после завершения сеанса пользователя:  
    - выключить ВМ;  
    - выключить ВМ принудительно (форсированно);  
    - приостановить ВМ.

Для автоматического и гостевого пулов существует также возможность копирования пула (настроек) с помощью кнопки **Копировать пул**.

При выборе вкладки **Виртуальные машины** в рабочей области отображается список 
имеющихся (созданных) в пуле ВМ, включая их названия, шаблон, имена пользователей, статусы и 
состояние гостевого агента. В окне доступны следующие операции:

- обновление информации;
- добавление ВМ. При нажатии на кнопку **Добавить ВМ** (доступна для статического пула) в 
открывшемся диалоговом окне необходимо из раскрывающегося списка выбрать свободную ВМ и 
подтвердить операцию, нажав кнопку **Добавить**; 
- удаление ВМ. При нажатии на кнопку **Удалить ВМ** (доступна для статического пула) в 
открывшемся диалоговом окне необходимо выбрать ВМ из раскрывающегося списка, подтвердить операцию, 
нажав кнопку **Удалить**;
- резервное копирование. При нажатии на кнопку **Резервное копирование** в открывшемся 
диалоговом окне необходимо подтвердить создание резервных копий всех виртуальных машин, нажав на кнопку **Выполнить**.
 
!!! note "Примечания"
    1. Добавление ВМ в автоматический и гостевой пулы происходит в соответствии с параметрами пула, 
    такими как: *Начальное количество ВМ*, *Шаг расширения пула*, 
    *Максимальное количество создаваемых ВМ в пуле*. Добавление ВМ происходит по 
    достижению порогового количества свободных ВМ, в количестве равном шагу расширения пула, 
    но не более максимального количества создаваемых ВМ.
    2. Удаляемая из статистического пула ВМ при этом остается в ECP VeiL без изменений.

Для просмотра параметров конкретной ВМ необходимо нажать на ее название, после чего 
откроется окно, в котором отобразится информация для этой ВМ. В окне становятся доступны следующие кнопки управления ВМ:

- назначить пользователя. При нажатии на кнопку ![image](../../_assets/common/user.png) в открывшемся диалоговом окне необходимо выбрать 
из раскрывающегося списка пользователей, после чего подтвердить операцию, нажав кнопку **Назначить**;
- освободить от пользователей. При нажатии на кнопку ![image](../../_assets/common/user_del.png) открывается окно с вопросом 
*Освободить ВМ от пользователей*. 
Для подтверждения операции необходимо нажать кнопку **Выполнить**;
- запустить ![image](../../_assets/common/start.png); 
- приостановить ![image](../../_assets/common/pause.png);
- выключение ![image](../../_assets/common/vm_stop.png);
- перезагрузка ![image](../../_assets/common/force_reboot.png);
- отключение питания ![image](../../_assets/common/poweroff.png);
- горячая перезагрузка ![image](../../_assets/common/hot_reboot.png);
- создание резервной копии ![image](../../_assets/common/copy.png);
- проверить нахождение в домене ![image](../../_assets/common/domen.png);
- монтировать образ VeiL utils;
- изменить шаблон. При нажатии все изменения на текущей ВМ будут применены к шаблону, из которого она была создана;
- преобразовать в шаблон. При нажатии ВМ перейдет в режим шаблона;
- зарезервировать ВМ. При включении ВМ зарезервируется для временного ограничения ее выдачи пользователям.

Более подробное описание ВМ приведено в [виртуальных машинах](domains.md).

При выборе вкладки **Пользователи** в рабочей области отображается список пользователей, 
имеющих доступ к выбранному пулу ВРС. В окне управления пользователями доступны следующие операции:

- обновление информации;
- добавление пользователя. При нажатии на кнопку **Добавить пользователя** в открывшемся диалоговом 
окне необходимо выбрать из раскрывающегося списка пользователя, после чего подтвердить операцию, 
нажав кнопку **Добавить**;
- удаление пользователя. При нажатии на кнопку **Удалить пользователя** в открывшемся диалоговом 
окне необходимо выбрать из раскрывающегося списка пользователя, после чего подтвердить операцию, 
нажав кнопку **Удалить**.

Более подробное описание пользователей и операции с ними приведены в [пользователях](users.md).

При выборе вкладки **Группы** в рабочей области отображается список групп пользователей, 
имеющих право пользования выбранным пулом ВРС. В окне управления группами доступны следующие операции:

- обновление информации;
- добавление группы. При нажатии на кнопку **Добавить группу** открывается окно выдачи группам прав пользования пулом, в котором необходимо выбрать из раскрывающегося списка одну или несколько групп. Для сохранения изменений необходимо нажать кнопку **Добавить**;
- удаление группы. При нажатии на кнопку **Удалить группу** открывается окно лишения групп права пользоваться пулом ВРС, в котором необходимо выбрать из раскрывающегося списка одну или несколько групп. Для подтверждения операции необходимо нажать кнопку **Удалить**.

Более подробное описание групп пользователей и операции с ними приведены в [группах](groups.md).
