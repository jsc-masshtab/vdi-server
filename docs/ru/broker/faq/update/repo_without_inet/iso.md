# Обновление с помощью установочного iso-образа 

Обновление с помощью установочного iso-образа является рекомендуемым способом.
Для обновления **VeiL Broker**, используя iso-образ, необходимо выполнить следующие действия:

1. Зайти в личный кабинет на портале АО «НИИ «Масштаб» https://lk.mashtab.org/ и сделать запрос на установочный iso-образ для нужной версии **VeiL Broker**.
2. Сохранить iso-образ на свой компьютер.
3. Загрузить iso-образ в Web-интерфейсе ECP VeiL на доступный пул данных и примонтировать его к ВМ, на которой установлен **VeiL Broker**.
4. Подключиться к ВМ, на которую установлен **Veil-Broker**, по протоколу SSH или по протоколу SPICE/VNC через Web-интерфейс 
   ECP VeiL и выполнить вход от имени учетной записи администратора (по умолчанию ** astravdi:Bazalt1!** ), указав значение **Integrity level** равное **_63_** или **Уровень целостности** - **_Высокий_** (для графического режима).
5. Запустить терминал, если вход был выполнен в графическом режиме;
6. В терминале выполнить команды для обновления **VeiL Broker**:
    
   `sudo mount /media/cdrom`    
   `cd`    
   `sudo bash /media/cdrom/install.sh`    
   `sudo umount /media/cdrom`
  
    

