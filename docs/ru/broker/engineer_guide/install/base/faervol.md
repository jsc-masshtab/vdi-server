# Настройка фаервола

Для настройки фаервола необходимо выполнить следующее:

- создать файл конфигурации фаервола c помощью команды

  `vim etc/ufw/aplications.d/vdi-broker`

- ввести следующую конфигурацию

  `[veil-broker]`

  `title=VeiL-broker`

  `description=Ports for VeiL-Broker`

  `ports=443,80/tcp`

- перезапустить фаервол c помощью команды

  `ufw reload`

- обновить конфигурацию и открыть порты, выполнив последовательно команды:

  `ufw reload`

  `ufw allow veil-broker`.

