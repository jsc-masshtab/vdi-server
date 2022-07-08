# Обновление VeiL Broker с 4.0.x на 4.1.x

1. Подключиться к ВМ, на которую установлен **Veil-Broker**, по протоколу SSH или по протоколу SPICE/VNC через Web-интерфейс **ECP VeiL**, 
   выполнить вход от имени учетной записи администратора (по умолчанию **astravdi:Bazalt1!** ), указав значение **Integrity level** 
   равное **63** или **Уровень целостности** - **Высокий** (для графического режима).
   
1. Прописать репозитории на серверах **VeiL Broker**. Для этого:

     - создать файл **veil-broker.list** с помощью команды
   
       `sudo mkdir /etc/apt/sources.list.d/veil-broker.list`
   
     - открыть его для редактирования с помощью команды
    
      `sudo nano /etc/apt/sources.list.d/veil-broker.list`

     - добавить путь к папке с обновлениями
    
      `deb http://veil-update.mashtab.org/veil-broker-prod-41 1.7_x86-64 main`

     - сохранить изменения, нажав **Ctrl+Х** и **Enter**.
 
1. Обновить списки пакетов с помощью команды
   `apt-get update`.

1. Выполнить обновление пакетной базы командой: `apt-get upgrade -y`.
