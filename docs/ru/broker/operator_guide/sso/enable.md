# Включение и отключение SSO

## Включение SSO

Для активации **SSO** необходимо выполнить следующие действия:

1. Поместить **keytab-файл** в каталог ```/etc/krb5.keytab```. Информация о том, как создать **keytab-файл**, содержится в разделе [Настройка службы каталогов](ad.md).
2. Задать соответствующие права доступа файлу ```/etc/krb5.keytab```, выполнив следующие команды:
    
    `chown root:www-data /etc/krb5.keytab`  
    `chmod 640 /etc/krb5.keytab`
    
3. В файл ```/etc/hosts``` добавить запись:
    ```
    192.168.6.64 astravdi.veil.team
    ```
   
    где ```192.168.6.64``` - IP-адрес брокера,
   
    ```astravdi.veil.team``` - доменное имя брокера.

4. Произвести настройку системы, выполнив следующую команду:

    ```
    sudo vdi_sso_settings -s HTTP/astravdi.veil.team@VEIL.TEAM -r VEIL.TEAM -i 10.0.0.1 -d veil.team -k /etc/krb5.keytab
    ```
   
    где ```HTTP/astravdi.veil.team@VEIL.TEAM``` - имя сервиса,
   
    ```VEIL.TEAM``` - имя области, которую покрывает Kerberos авторизация,
   
    ```10.0.0.1``` - ip-адрес сервера службы каталогов, на котором развернута служба, 
   
    ```veil.team``` - доменная зона, 
    
    ```/etc/krb5.keytab``` путь к keytab-файлу. 

    !!! attention "Внимание!"
         Имя сервиса должно включать имя области Kerberos и иметь вид: ```HTTP/astravdi.veil.team@VEIL.TEAM``` !

5. В Web-интерфейсе брокера в разделе **Настройки** - **Службы каталогов**, выбрать подключенную службу каталогов, нажать кнопку **Конфигурация SSO**, 
   поставить галочку и нажать **Изменить**.

## Выключение SSO

Для выключения SSO достаточно в Web-интерфейсе брокера в разделе **Настройки** - **Службы каталогов**, выбрать подключенную службу каталогов, нажать кнопку **Конфигурация SSO**, снять галочку и нажать **Изменить**.

Для удаления настроек SSO необходимо выполнить команду 

```vdi_sso_settings --disable```