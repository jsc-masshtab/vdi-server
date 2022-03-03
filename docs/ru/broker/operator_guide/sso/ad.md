# Настройка службы каталогов

## MS AD

1. Добавить пользователя с правами администратора. Для функционирования **SSO** необходимо в службе каталогов создать пользователя с правами администратора и неограниченным временем действия пароля, например **vdi-sso**, от имени которого будет происходить проверка пользователя при получении доступа к Web-интерфейсу брокера.

2. В DNS зону, добавляем A-запись брокера, например имя: ```astravdi``` и FQDN имя ```astravdi.veil.team```.

3. Добавить службу на сервере MS AD выполнив следующую команду:
   ```
   setspn.exe -A HTTP/astravdi.veil.team@VEIL.TEAM  vdi-sso
   ```
   , где ```HTTP/astravdi.veil.team@VEIL.TEAM``` - имя службы, ```vdi-sso``` - пользователь, от имени которого будет происходить проверка.

4. Сгенерировать в MS AD **keytab-файл** выполнив в CMD сервера AD команду:

```
ktpass.exe /princ HTTP/astravdi.veil.team@VEIL.TEAM /mapuser vdi-sso@VEIL.TEAM /crypto ALL /ptype KRB5_NT_PRINCIPAL /mapop set /pass Bazalt1! /out c:\krb5.keytab
```
, где ```HTTP/astravdi.veil.team@VEIL.TEAM``` название службы авторизации, ```vdi-sso@VEIL.TEAM``` и ```Bazalt1!``` имя и пароль пользователя MS AD, от имени которой будет происходить проверка пользователей, ```c:\krb5.keytab``` путь, по которому создастся файл.

## Free IPA

1. В консоли сервера **Free IPA** от имени пользователя с правами администратора службы каталогов создать службу авторизации, выполнив следующие команды:
```
kinit admin
ipa service-add HTTP/astravdi.veil.team
```
, где ```admin```  - имя пользователя с правами администратора.

2. В консоли сервера **Free IPA** создать **keytab-файл** от имени пользователя с правами администратора выполнив следующие команды:
```
kinit admin
ipa-getkeytab -p HTTP/astravdi.bazalt.auth -k /tmp/krb5.keytab
```
, где ```admin```  - имя пользователя с правами администратора.

3. В DNS зону, добавляем A-запись брокера, например имя: ```astravdi```.