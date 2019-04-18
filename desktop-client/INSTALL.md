# **Windows:** 

`работает на Python 2.7`

- Устанавливаем `pygobject` по [руководству](https://pygobject.readthedocs.io/en/latest/getting_started.html#windows-logo-windows),
но для Python 2.7 (5. Execute pacman -S mingw-w64-i686-gtk3 mingw-w64-i686-`python`-gobject)

`далее работаем в MinGW 32-bit`

- Ставим pip:

```
pacman -S mingw32/mingw-w64-i686-python-pip
```

- Ставим vdi_thin_client_us2.7 requirements:

```
python -m pip install -r /<desktop-client_path>/requirements.txt
```

- Ставим SPICE пакеты (32-bit) для GTK:

```
pacman -S mingw32/mingw-w64-i686-spice-gtk mingw32/mingw-w64-i686-spice-protocol
``` 

# **Linux:**

`работает на Python 2.7`

```
sudo apt install libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0
pip install pipenv
cd <desktop-client>
pipenv install
```

