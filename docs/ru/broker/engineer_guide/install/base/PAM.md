# Настройка PAM

Описанная ниже информация носит рекомендательный характер. Обратите внимание, что данные настройки могут привести к
полной блокировке доступа в систему.

!!! note "PAM"
    Pluggable Authentication Modules (**PAM**, подключаемые модули аутентификации) — это набор разделяемых библиотек, 
    которые позволяют интегрировать различные низкоуровневые методы аутентификации в виде единого высокоуровневого API.

При стандартной установке **VeiL Broker** параметр **PAM_AUTH** выключен (начиная с версии 4.0.0).

За основу настройки **PAM** в системе можно взять следующий пример:

!!! example "/etc/pam.d/common-auth"
    `# force vdi-web check`    
    `auth required pam_succeed_if.so user ingroup vdi-web`
        

!!! example "/etc/pam.d/login"
    `# change default delay`    
    `auth optional pam_faildelay.so delay=1000000`

!!! warning "Предупреждение"
    Не забудьте добавить в указанную группу пользователя, под которым выполняется вход в GUI для администрирования.

Дальнейшее описание работы с системой авторизации доступно [здесь](../../../auth_v3/info.md).