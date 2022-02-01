# Общие сведения

Текущая конфигурация **VeiL Connect** для пользователя хронится в файле настроек. Если файл настроек отсутствует, он будет автоматически создан при первом запуске **VeiL Connect** и будет содержать в себе стандартные настройки. Изменять конфигурацию можно в приложении **VeiL Connect** или путем редактирования файла настроек с последующим перезапуском приложения **VeiL Connect** для применения новых настроек.

В данном разделе описаны параметры и их значения в конфигурационном файле **VeiL Connect**.

В операционных системах семейства **Linux** конфигурационные файлы находятся по адресу:
```
/home/{текущий пользователь}/.config/VeilConnect
```

В операционных системах семейства **Windows** конфигурационные файлы находятся по адресу:

```
C:\Users\{текущий пользователь}\AppData\Local\VeilConnect
```

Файлы настроек:
  - veil_client_settings.ini. Файл настроек приложения в стандартном ini формате.
  - x2go_data/x2go_sessions. Файл настроек x2go. Автоматически создается в момент подключения по протоколу x2go для использования x2go клииентом.
  - rdp_data/rdp_file.rdp. Файл настроек RDP. Автоматически создается в момент подключения по протоколу Native RDP для использования нативным клииентом. (ОС Windows и MacOS).

!!!info "Настройка **VeiL Connect** в окне программы"
Подробная информация о настройке приложения **VeiL Connect** в окне программы содержится в разделе [Настройки](../settings/main_settings.md).