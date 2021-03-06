# Группа настроек RDPSettings

В таблице представлены описания настроек **RDP** и их возможные значения.

| Параметр                | Описание                                                                       | Возможные значения                                        |
|-------------------------|--------------------------------------------------------------------------------|-----------------------------------------------------------|
| rdp_fps                 | Частота обновления картинки (Перерисовки экрана)                               | Число 1-60                                                |
| is_rdp_vid_comp_used    | Использовать ли сжатие видеопотока                                             | 1/0                                                       |
| rdp_vid_comp_codec      | Используемый кодек. Учитывается только если is_rdp_vid_comp_used равно 1       | AVC420/AVC444/RemoteFX                                    |
| rdp_shared_folders      | Перенаправляемые папки. Пути, перечисленные через точку с запятой без пробелов | строка                                                    |
| is_multimon             | Мультимониторность                                                             | 1/0                                                       |
|full_screen              | Активен ли режим полного экрана                                                | 1/0                                                       |
|selectedmonitors         | Указать, какие клиентские мониторы должны использоваться для отображения удаленного рабочего стола. Мониторы должны иметь обшие стороны.  |Параметр задается как список id мониторов через запятую. Пример 0,1|
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
| rdp_args                | Список параметров freerdp                                                      | Список параметров freerdp через запятую                           |

!!! note "Примечание" 
 - Конфигурация мониторов для RDP определяется параметром RDPSettings/selectedmonitors. 
 Указывает, какие клиентские мониторы должны использоваться для отображения удаленного рабочего стола.
 Мониторы должны иметь обшие стороны. Параметр задается как список id мониторов через запятую.
 Например: 0,1 - использовать мониторы с id 0 и 1.
 - Для сквозной передачи параметров FreeRDP используется параметр RDPSettings/rdp_args.     