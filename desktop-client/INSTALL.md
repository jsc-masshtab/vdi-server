**Windows:** 

`работает только на Python 2.7`

- Устанавливаем `pygobject` по [руководству](https://pygobject.readthedocs.io/en/latest/getting_started.html#windows-logo-windows),
но для Python 2.7 (5. Execute pacman -S mingw-w64-i686-gtk3 mingw-w64-i686-`python`-gobject)

`далее работаем в MinGW 32-bit`

- Ставим pip:

```
pacman -S mingw32/mingw-w64-i686-python-pip
```

- Ставим vdi_thin_client_us2.7 requirements:

```
python -m pip install -r /<path_to_vdi_thin_client-us2.7>/requirements.txt
```

- Ставим SPICE пакеты (32-bit) для GTK:

```
pacman -S mingw32/mingw-w64-i686-spice-gtk mingw32/mingw-w64-i686-spice-protocol
```

**Linux:**

`работает на Python >= 2.7`

- Устанавливаем `pygobject` по соответствующему [руководству](https://pygobject.readthedocs.io/en/latest/getting_started.html#ubuntu-logo-ubuntu-debian-logo-debian)

