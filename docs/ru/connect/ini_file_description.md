# Описание ini файла настроек

##Группа General

| Параметр        | Описание                                                                                                                                                                                  | Возможные значения |
|-----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------|
| opt_manual_mode | Если 0, то стандартный режим подключения к VDI серверу (Авторизация на VeiL VDI). Если 1, то подкючение напрямую к ВМ. Для подключения используются данные из группы RemoteViewerConnect  | 1/0                |

                      


##Группа RemoteViewerConnect

| Параметр                         | Описание                                                                                                 | Возможные значения |
|----------------------------------|----------------------------------------------------------------------------------------------------------|--------------------|
| ip                               | Адрес подключения                                                                                        | строка             |
| username                         | Логин                                                                                                    | строка             |
| password                         | Пароль                                                                                                   | строка             |
| port                             | Порт                                                                                                     | Число 1-65535      |
| domain                           | Доменное имя. Может быть пустым                                                                          | строка             |
| is_ldap_btn_checked              | Используется ли LDAP                                                                                     | 1/0                |
| is_conn_to_prev_pool_btn_checked | Подключаться ли к предыдущему выбранному пулу (пул, к которому пользователь подключался в последний раз) | 1/0                |
| to_save_pswd                     | Сохранять ли пароль в ini файл                                                                           | 1/0                |



##Группа SpiceSettings

| Параметр                         | Описание                               | Возможные значения |
|----------------------------------|----------------------------------------|--------------------|
| is_spice_client_cursor_visible   | Отображать ли клиентский курсор        | 1/0                |



##Группа RDPSettings

| Параметр                | Описание                                                                       | Возможные значения                                        |
|-------------------------|--------------------------------------------------------------------------------|-----------------------------------------------------------|
| rdp_fps                 | Частота обновления картинки (Перерисовки экрана)                               | Число 1-60                                                |
| is_rdp_vid_comp_used    | Использовать ли сжатие видеопотока                                             | 1/0                                                       |
| rdp_vid_comp_codec      | Используемый кодек. Учитывается только если is_rdp_vid_comp_used равно 1       | AVC420/AVC444/RemoteFX                                             |
| rdp_shared_folders      | Перенаправляемые папки. Пути, перечисленные через точку с запятой без пробелов | строка                                                    |
| is_multimon             | Мультимониторность                                                             | 1/0                                                       |
| redirect_printers       | Перенаправлять ли принтеры                                                     | 1/0                                                       |
| is_remote_app           | Запускать ли приложение при подключении                                        | 1/0                                                       |
| remote_app_name         | Имя запускаемого приложения. Учитывается только если is_remote_app равно 1     | строка                                                    |
| remote_app_options      | Опции запускаемого приложения. Учитывается только если is_remote_app равно 1   | строка                                                    |
| is_rdp_network_assigned | Указывать ли тип сети                                                          | 1/0                                                       |
| rdp_network_type        | Тип сети. Учитывается только если is_rdp_network_assigned равно 1              | modem/broadband/broadband-low/broadband-high/wan/lan/auto |
| disable_rdp_decorations | Выключить ли оформления окон                                                   | 1/0                                                       |
| disable_rdp_fonts       | Выключить ли гладкие шрифты                                                    | 1/0                                                       |
| disable_rdp_themes      | Выключить ли Windows темы                                                      | 1/0                                                       |
| rdp_pixel_format        | Формат изображения                                                             | BGRA16/BGRA32                                             |

## Пример
```
[General]
opt_manual_mode=0

[RemoteViewerConnect]
username=AD666
password=pass!1
domain=
ip=192.168.87.5
port=443

is_ldap_btn_checked=0
is_conn_to_prev_pool_btn_checked=0
to_save_pswd=1

[SpiceSettings]
is_spice_client_cursor_visible=1

[RDPSettings]
rdp_fps=30
rdp_vid_comp_codec=1
rdp_vid_comp_codec=AVC420
rdp_shared_folders=/home/ubuntu/job
is_multimon=0
redirect_printers=0
is_remote_app=0
remote_app_name=
remote_app_options=
is_rdp_network_assigned=0
rdp_network_type=auto
disable_rdp_decorations=0
disable_rdp_fonts=0
disable_rdp_themes=0
rdp_pixel_format=BGRA32
```