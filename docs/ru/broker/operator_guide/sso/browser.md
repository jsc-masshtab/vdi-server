#  Настройка браузера для работы с SSO

Для того. чтобы сквозная авторизация SSO работала необходимо настроить браузер для передачи данных учетной записи при подключении к Web-интерфейсу брокера.

## Internet Explorer и EDGE

Откройте Свойства браузера -> Безопасность -> Местная интрасеть (Local intranet), нажмите на кнопку Сайты -> Дополнительно. Добавьте в зону следующую запись: ```https://*.veil.team```.

!!!info "Групповые политики MS AD"
    Добавить сайты в эту зону можно с помощью групповой политики: Computer Configuration ->Administrative Templates ->Windows Components -> Internet Explorer -> Internet Control Panel -> Security Page -> Site to Zone Assignment. Для каждого веб-сайта нужно добавить запись со значением 1.

Далее перейдите на вкладку Дополнительно (Advanced) и в разделе Безопасность (Security) убедитесь, что включена опция Разрешить встроенную проверку подлинности Windows (Enable Integrated Windows Authentication).

!!!warning "Внимание"
    Убедитесь, что брокер присутствует только в зоне Местная интрасеть. Для сайтов, включенных в зону Надежные сайты (Trusted sites), токен Kerberos не отправляется на соответствующий веб-сервер.

## Mozilla Firefox

По умолчанию поддержка Kerberos в Firefox отключена, чтобы включить ее, откройте окно конфигурации браузера (в адресной строке перейдите на адрес ```about:config```). Затем в следующих параметрах укажите адрес брокера.
```
network.negotiate-auth.trusted-uris
network.automatic-ntlm-auth.trusted-uris
```