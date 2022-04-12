# Добавление пользователей в группу удалённых рабочих столов для подключения по RDP к ВМ

Для добавления пользователей в группу удалённых рабочих столов для подключения по RDP к ВМ необходимо выполнить следующие действия:

1. Для создания пользователей в шаблоне ВМ необходимо перейти в оснастку Windows **Управление компьютером**. Для этого необходимо зайти в ВМ с административной учётной записью и выполнить в командной строке команду `compmgmt.msc`. 
2. В разделе **Управление компьютером** перейти в подраздел  **Локальные пользователи и группы → Пользователи**.
3. Создать необходимое количество локальных пользователей.
4. Для добавления созданных локальных пользователей в группу удалённых рабочих столов перейти в раздел **Управление компьютером → Локальные пользователи и группы → Пользователи → Пользователи удалённого рабочего стола**. 
5. В окне **Свойства: Пользователи удалённого рабочего стола** добавить пользователей в группу.