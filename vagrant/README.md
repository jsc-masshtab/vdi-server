
**Создание/обновление бокса**

```
./vagrant.py setup
```

**Полное удаление бокса**

```
./vagrant.py purge
```

**Копирование бокса**

(последней версии "generic/ubuntu1904" в vdihost)

```
./vagrant.py copyimage
```

**Конфиг**

лежит в `vagrant/base/config.json.template` 

```json
{
  "boxname": "vdihost",
  "hostname": "vdihost",
  "image": "generic/ubuntu1904"
}
```

для модификации нужно сначала переименовать в `config.json`:

```
cp vagrant/base/config.json.template vagrant/base/config.json
```


**Обновление бокса вручную**

1. Создаём конфиг-файл

```
cp vagrant/base/config.json.template vagrant/base/config.json
```

2.  Проверяем, обновился ли бокс "generic/ubuntu1904"

```
cd vagrant/base/box
vagrant box update
```

3. Если на предыдущем шаге скачан новый бокс версии `<current version>`, сохраняем его под именем `vdihost`

```
cp -r ~/.vagrant.d/boxes/generic-VAGRANTSLASH-ubuntu1904/<current version>/libvirt ~/.vagrant.d/boxes/vdihost/<current version>/libvirt
```

4. Обновляем и устанавливаем пакеты с помощью `apt`:

```
cd vagrant/base
vagrant up
vagrant destroy -f
```

5. Поднимаем нашу целевую ВМ

```
# в корневой директории проекта
vagrant up
```