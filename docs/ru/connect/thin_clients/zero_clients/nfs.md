# Настройка NFS

1. Установить программу nfs-utils командой:

    !!! example "Для дистрибутивов использующих менеджер пакетов apt"
        ```
        sudo apt-get install nfs-utils
        ```
    
    !!! example "Для дистрибутивов использующих менеджер пакетов yum"
        ```
        sudo yum install nfs-utils
        ```

2. Добавить в файл конфигурации программы nfs-utils '/etc/exports' следующую строку, содержащую путь к публикуемой директории, 
   содержащий образ ISO.

    `/srv/public -ro,insecure,no_subtree_check,fsid=1 *`
   
3. Перенести образ ISO в директорию, указанною в конфигурации NFS командой:

    `mv /patch-to-iso/live-veil-connect-<version>.iso /srv/public/`
