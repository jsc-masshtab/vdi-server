import { VmsService } from '../all-vms/vms.service';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

interface ICollection {
  [index: string]: string;
}

@Component({
  selector: 'vdi-vm-details',
  templateUrl: './vm-details.component.html',
  styleUrls: ['./vm-details.component.scss']
})


export class VmDetailsComponent implements OnInit, OnDestroy {

  public vm: ICollection = {};

  public collectionDetails = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'desktop',
      type: 'string'
    },
    {
      title: 'Описание',
      property: 'description',
      type: 'string'
    },
    {
      title: 'Состояние',
      property: 'user_power_state',
      type: 'string'
    },
    {
      title: 'IP адрес',
      property: 'address',
      type: 'array'
    },
    {
      title: 'Имя хоста',
      property: 'hostname',
      type: 'string'
    },
    {
      title: 'Процессоры',
      property: 'cpu_count',
      type: 'string'
    },
    {
      title: 'Оперативная память',
      property: 'memory_count',
      type: 'string'
    },
    {
      title: 'Операционная система',
      property: 'os_type',
      type: 'string'
    },
    {
      title: 'Версия операционной системы',
      property: 'os_version',
      type: 'string'
    },
    {
      title: 'Шаблон',
      property: 'parent_name',
      type: 'string'
    },
    {
      title: 'Пул ресурсов',
      property: 'resource_pool',
      property_lv2: 'verbose_name',
      type: 'string'
    },
    {
      property: 'tablet',
      title: 'Режим планшета',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'spice_stream',
      title: 'SPICE потоки',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'ha_enabled',
      title: 'Высокая доступность',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'disastery_enabled',
      title: 'Катастрофоустойчивость',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'guest_agent',
      title: 'Гостевой агент',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'remote_access',
      title: 'Удаленный доступ',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      property: 'start_on_boot',
      title: 'Автоматический запуск ВМ',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включено', 'Выключено']
      }
    },
    {
      title: 'Тип загрузочного меню',
      property: 'boot_type',
      type: 'string'
    },
    {
      title: 'Тэги',
      property: 'domain_tags',
      type: {
        typeDepend: 'tags_array'
      }
    }
  ];

  public idVm: string;
  public menuActive: string = 'info';
  public host: boolean = false;
  private address: string;
  private sub: Subscription;

  constructor(private activatedRoute: ActivatedRoute,
              private service: VmsService,
              private router: Router) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.idVm = param.get('id') as string;
      this.address = param.get('address');
      this.getVM();
    });
  }

  public getVM() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
    this.host = false;
    this.sub = this.service.getVm(this.idVm, this.address).valueChanges.pipe(map(data => data.data.vm))
      .subscribe((data) => {
        this.vm = data;
        this.host = true;
      },
      () => {
        this.host = true;
      });
  }

  public close() {
    this.router.navigate(['pages/resourses/vms']);
  }

  public routeTo(route: string): void {
    if (route === 'info') {
      this.menuActive = 'info';
    }
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }
}
