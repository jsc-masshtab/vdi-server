# Отключение механизмов AUTH Astra Linux

В сценарии использования, при котором нет необходимости задействовать **PAM**-аутентификацию, целесообразно деактивировать
данный параметр в приложении. Деактивация существенно увеличит производительность механизма AUTH.

Для этого в файле настроек `/opt/veil-vdi/app/common/local_settings.py` необходимо
заменить стандартные значения ключей `LOCAL_AUTH` и `PAM_AUTH` на: 

`LOCAL_AUTH = True`
  
`PAM_AUTH = False`

!!! warning "Предупреждение"
    Параметры являются взаимоисключающими, поэтому редактировать нужно оба.

После установки параметров необходимо перезапустить службы системы либо выполнить полную перезагрузку сервера (службы
 запускаются в автоматическом режиме).

!!! warning "Предупреждение"
    Отключение параметра `PAM_AUTH`, как правило, делает невозможным автоматическое включение его обратно, т.к. между 
    пользователями системы (Astra Linux) и брокера появится расхождение.