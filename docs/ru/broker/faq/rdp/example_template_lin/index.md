# Общие сведения
## Протоколы удалённого доступа для Linux
Для предоставления удалённого доступа в ОС Linux наиболее часто используемыми протоколами являются VNC, SPICE и RDP
Протоколы SPICE и VNC ужк реализованы на уровне гипервизора в среде VEIL/VDI.
При подключении к ВМ по этим протоколам Брокер использует параметры, хранимые в среде VEIL/VDI.

Так же для всех ВМ в среде VEIL/VDI предусмотрен доступ по протоколу RDP, но для ОС Linux необходимо установить RDP сервер.

Для установки RDP сервера рекомендуется использовать: xrdp + xorgxrdp + pulseaudio-module-xrdp.

Семейство Debian/Ubuntu:  
```# sudo apt install xrdp xorgxrdp pulseaudio-module-xrdp```

Семейство ReHat/CentOs:  
```# sudo yum install xrdp xorgxrdp pulseaudio-module-xrdp```
