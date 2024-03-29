# Перенаправление папок по Spice

Текущий пользователь должен иметь право на перенаправление папок (Задается администратором в Web-интерфейсе 
[Разрешения](../../broker/auth_v3/client-permissions.md)). 

##VeiL Connect запущен на хосте с Linux/Windows. На ВМ установлен Linux

### На ВМ установлен файловый менеджер с поддержкой технологии WebDAV (например nautilus)
    
- В гостевой ВМ установить **spice-webdavd service** командой `sudo apt install spice-webdavd`.
- Запустить сервис командой `sudo spice-webdavd -p 8000`.
- Перезапустить ВМ.
- С **VeiL Connect** подключиться к ВМ.
- В меню **Настройки** выбрать **Общие папки**. В открывшемся окне выбрать папку 
    для перенаправления.
- Поставить "галочку" **Общая папка**. Закрыть окно.
- В сетевых папках ВМ появится пункт **Spice client folder**. Нажать на него, чтобы 
      открыть общую папку.

### На ВМ установлен файловый менеджер без поддержки технологии WebDAV (например fly-fm)

####Вариант 1
- В гостевой ВМ установить **spice-webdavd service** командой 
      `sudo apt install spice-webdavd`.
- Запустить сервис командой `sudo spice-webdavd -p 9843`.
- В **VeiL Connect** в меню **Настройки** выбрать **Общие папки**. В открывшемся окне выбрать папку 
    для перенаправления.
- Поставить "галочку" **Общая папка**. Закрыть окно.
- В гостевой ВМ установить davfs2, выполнив команду `sudo apt-get install davfs2`.
- Создать директорию для монтирования, например `sudo mkdir /home/m`.
- Монтировать папку: `sudo mount -t davfs http://127.0.0.1:9843 /home/m`
- В папке /home/m отобразится содержимое проброшенной папки.

####Вариант 2
- Установить файловый менеджер nautilus.
- Отключить IPv6, выполнив в терминале команды:

```
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
```

```
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
```

```
sudo sysctl -w net.ipv6.conf.lo.disable_ipv6=1
```

- Далее следовать инструкции для файлового менеджера с поддержкой технологии WebDAV.

##VeiL Connect запущен на хосте с Linux/Windows. На ВМ установлен Windows

- В гостевой ВМ установить 
    [spice-webdavd-x64-latest](https://www.spice-space.org/download/windows/spice-webdavd/).
- Открыть командную строку, перейти в папку **C:\Program Files\SPICE webdavd** и выполнить скрипт 
      **map-drive.bat**.
- С **VeiL Connect** подключиться к ВМ.
- В меню **Настройки** выбрать **Общие папки**. В открывшемся окне выбрать папку 
    для перенаправления.
- Поставить "галочку" **Общая папка**. Закрыть окно.
- В ВМ появится новый сетевой диск **Spice client**, на котором будет содержимое общей папки.
