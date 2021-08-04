## Возможные ошибки

#### Веб-интерфейс не работает или невозможно залогиниться

Проверьте в терминале ВМ, включен ли apache2

```bash
sudo systemctl status apache2
```
   
Если он не включен, то включить и выполнить:

```bash
sudo systemctl start apache2
sudo chown www-data:adm /var/log/apache2 -R
```

Такая ошибка может возникать после перезагрузки ВМ в версиях 3.1.0 и ниже