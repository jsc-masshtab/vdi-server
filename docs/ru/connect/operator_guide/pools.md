# Окно доступных пулов ВМ

После успешной авторизации и настройки параметров соединения пользователь 
переходит в окно доступных пулов ВМ, в верхней части которого расположены кнопки 
**Обновить** и **Выйти**, а в нижней части - статусная строка, в
которую выводятся информационные сообщения о функционировании программы.

Главная рабочая область окна содержит список доступных пулов ВМ с 
предустановленными протоколами подключения к ВРС.

#### Протоколы подключения к ВРС

- Протокол Spice используется тогда, когда подключение к ВМ производится 
средствами ECP VeiL. На стороне ECP VeiL на каждом узле, на котором запускаются ВМ, 
реализован *Spice-server*. Подключение происходит через контроллер ECP VeiL,
что требует наличия сетевой доступности контроллера ECP VeiL для клиентского 
устройства, с которого производится подключение к ВМ. При выборе *Spice_direct* 
подключение произойдет также по протоколу Spice, но напрямую к узлу, где находится ВМ.
- RDP-native вызывает встроенный Windows-клиент *mstsc.exe*.
- RDP использует собственную реализацию RDP-клиента.

ОС Windows в ВМ должна быть предварительно настроена администратором или средствами Group Policy домена AD на прием 
подключений по протоколу RDP для пользователя AD, с которым будет подключаться пользователь.
    
Графическое изображение изменяется в зависимости от состояния, в котором находится пул, 
который может быть помечен текстовыми полями *CREATING* и *FAILED*. Если пул создается, 
то он помечается надписью *CREATING*. Если пул недоступен, то он помечается красным 
прямоугольником, содержащим надпись *FAILED*. Если пул находится в рабочем 
состоянии, то он активен для выбора пользователем.
    
Для загрузки доступного пула необходимо нажать на его графическое изображение. 
Программа отправит запрос на получение ВМ из пула и, если в составе пула у пользователя 
есть доступ к ВМ, то произойдет ее подключение и запуск. Если ВМ не 
удалось получить из пула или в пуле нет свободных ВМ, то соответствующее сообщение 
появится в статусной строке рабочей области окна.

В окне существует возможность обновить список доступных пулов ВМ с помощью кнопки **Обновить**.

Выход из окна осуществляется при нажатии на кнопку **Выход**.

!!! note "Примечание"
    Если при попытке подключения к пулу по RDP появилось сообщение 
    *Нет соединения ERRCONNECT_LOGON_FAILURE*, это значит, что либо ВМ не добавлена в тот же домен 
    что и пользователь, либо учетная запись на ВМ не совпадает с учетной записью на VDI брокере (логин/пароль).
