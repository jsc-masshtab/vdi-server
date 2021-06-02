# Условия выполнения программы

Для нормального функционирования VeiL Connect E требуется ПЭВМ, технические характеристики 
которой не должны уступать приведенным ниже:

- процессор с частотой не менее 1 ГГц;
- объем оперативной памяти – не менее 1 Гбайт (для 32-bit системы) и не менее 2 Гбайт (для 64-bit системы);
- свободное дисковое пространство не менее 130 Мб;
- постоянное запоминающее устройство – не менее 1 Гбайт;
- интерфейсы сетевые – не менее 1 Гбит Ethernet, в количестве не менее одного.

Для нормального функционирования VeiL Connect E на ОС Linux требуется наличие общесистемных 
программных средств среды функционирования прикладных программ ОС Linux семейства Debian/Ubuntu 
и следующих пакетов:

1. процессор с архитектурой х86:
   - libhiredis-dev;
   - libspice-client-gtk-3.0-dev;
   - libjson-glib-dev;
   - libxml2-dev;
   - libsoup2.4-dev;
   - freerdp2-dev;
   - gcc;
   - cmake;
   - pkg-config;
   - libusb-1.0-0-dev;
   - libusbredirparser-dev;

1. процессор с архитектурой e2k-8c:
   - spice-client-gtk;
   - libspice-client-gtk-3.0-dev;
   - libjson-glib-dev;
   - libxml2-dev;
   - libsoup2.4-dev;
   - freerdp2-dev;
   - libfreerdp-client2-2;
   - libwinpr2-2;
   - libwinpr2-dev;
   - cmake;
   - pkg-config;
   - binutils-dev;
   - binutils;
   - dprof;
   - gcov;
   - gdb;
   - lcc-1.23;
   - libc-dev-bin;
   - libc6-dev-e2k32;
   - libc6-dev;
   - libstdc++6-e2k32;
   - linux-libc-dev;
   - locales-all;

1. процессор с архитектурой miplsel (*Таволга Терминал*):
   - rpm-build;
   - libspice-gtk3-devel;
   - libfreerdp-devel;
   - libjson-glib-devel;
   - libsoup-devel;
   - libxml2-devel;
   - gcc;
   - cmake;
   - make;
   - libhiredis-devel;
   - libusbredir-devel;
   - libusb-devel. 
 
!!! note "Примечание" 
    Часть перечисленных пакетов устанавливается вместе с графической оболочкой ОС.

При установке VeiL Connect E на ОС Linux все необходимые зависимости установятся автоматически из 
стандартного источника пакетов ОС.
 
Специалист, производящий установку VeiL Connect E, должен иметь навыки работы на ПЭВМ в 
ОС Linux семейства Debian/Ubuntu.
