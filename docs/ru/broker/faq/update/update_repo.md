# Обновление VeiL Broker с внешнего репозитория

!!! note "Примечание"
    Проверить текущую версию **VeiL Broker** и его компонентов можно командой `dpkg -l | grep veil`.

!!! warning "Предупреждение"
    Во время обновления сервис будет недоступен. Следует выбрать допустимое время и выполнить резервное копирование ВМ.

Для обновления **VeiL Broker**, используя внешний репозиторий, необходимо выполнить следующие действия:

1. 1) Подключиться по SSH командой 

      `ssh <имя пользователя>@<IP-адрес машины, на которой установлен VeiL Broker>`
    
      Пример команды: `ssh astravdi@192.168.7.17`

    или 

    2) Войти в систему, указав значение **Integrity level** равное **63** или 
   **Уровень целостности** - **Высокий** (для графического режима).
   
    !!! note "Стандартные репозитории пакетов"
        Если при установке были пропущены шаги по копированию стандартных дистрибутивов Astra Linux, 
        следует ознакомиться с шагами по копированию **основного** и **devel** дисков 
        в разделе [Установка и настройка ОС](../../engineer_guide/install/prepare/install_os.md).

1. Подключить внешний репозиторий **VeiL Broker**:

    ```
    echo "deb https://veil-update.mashtab.org/veil-broker-prod-32 smolensk main" | sudo tee /etc/apt/sources.list.d/vdi.list
    ```
    где указана свежая версия репозитория с [сайта доступных версий](https://veil-update.mashtab.org/).
 
1. Выполнить команды для обновления:

    `sudo apt-get update`
     
    `sudo apt-get upgrade -y`
     
    `sudo rm -f /etc/apt/sources.list.d/vdi.list`
     
    `sudo apt-get update`
     
    !!! info "Просроченный корневой сертификат"
         Если при выполнении команды `sudo apt-get update` происходит ошибка 
         **"Данные из этого репозитория нельзя аутентифицировать, и поэтому потенциально 
         из небезопасно использовать"** \* необходимо выполнить следующие команды и повторить 
         процесс обновления:  
         `sudo sed -i '/mozilla\/DST_Root_CA_X3.crt/s/^/#/' /etc/ca-certificates.conf`  
         `sudo update-ca-certificates --fresh`  
         \* Орфография и пунктуация автора сохранены.

1. Перезапустить ВМ, на которой установлен **VeiL Broker**.  


