import { TemplatesService } from '../all-templates/templates.service';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { map } from 'rxjs/operators';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import {YesNoFormComponent} from '../../../../common/forms-dinamic/yes-no-form/yes-no-form.component';

interface ICollection {
  [index: string]: string;
}

@Component({
  selector: 'vdi-template-details',
  templateUrl: './template-details.component.html',
  styleUrls: ['./template-details.component.scss']
})


export class TemplateDetailsComponent implements OnInit, OnDestroy {

  public template: ICollection = {};

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
      title: 'Процессоры',
      property: 'cpu_count',
      type: 'string'
    },
    {
      title: 'Оперативная память',
      property: 'memory_count',
      type: 'bites',
      delimiter: 'Мб'
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
      title: 'Статус',
      property: 'status',
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

  public idTemplate: string;
  public menuActive: string = 'info';
  public host: boolean = false;
  private address: string;
  private sub: Subscription;

  constructor(private activatedRoute: ActivatedRoute,
              private service: TemplatesService,
              private router: Router,
              public dialog: MatDialog) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.idTemplate = param.get('id') as string;
      this.address = param.get('address') as string;
      this.getTemplate();
    });
  }

  public getTemplate() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
    this.host = false;
    this.sub = this.service.getTemplate(this.idTemplate, this.address).valueChanges.pipe(map(data => data.data.template))
      .subscribe((data) => {
        this.template = data
        this.host = true;
      },
      () => {
        this.host = true;
      });
  }

  public attachVeilUtils() {
    this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: 'Подтверждение действия',
            question: `Монтировать образ VeiL utils для шаблона ${this.template.verbose_name}?`,
            button: 'Выполнить'
          },
          request: {
            service: this.service,
            action: 'attachVeilUtils',
            body: {
              id: this.idTemplate,
              controller_id: this.address
            }
          }
        }
      })
  }

  public close() {
    this.router.navigate(['pages/resourses/templates']);
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
