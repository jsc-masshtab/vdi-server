import { AddUserVmComponent } from './add-user/add-user.component';
import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog } from '@angular/material';
import { RemoveUserVmComponent } from './remove-user/remove-user.component';
import { YesNoFormComponent } from 'src/app/dashboard/common/forms-dinamic/yes-no-form/yes-no-form.component';
import { PoolDetailsService } from '../pool-details.service';


@Component({
  selector: 'vdi-details-popup',
  templateUrl: './vm-details-popup.component.html'
})

export class VmDetalsPopupComponent {

  public offset = 0;

  public menuActive: string = 'info';
  public testing: boolean = false;
  public tested: boolean = false;
  public connected: boolean = false;
  public collectionIntoVmAutomated: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string'
    },
    {
      title: 'Шаблон',
      property: 'parent_name',
      type: 'string'
    },
    {
      title: 'Пользователь',
      property: 'user',
      property_lv2: 'username'
    },
    {
      title: 'Состояние',
      property: 'user_power_state',
      type: 'string'
    },
  ];

  public collectionIntoVmStatic: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string'
    },
    {
      title: 'Шаблон',
      property: 'parent_name',
      type: 'string'
    },
    {
      title: 'Пользователь',
      property: 'user',
      property_lv2: 'username'
    },
    {
      title: 'Состояние',
      property: 'user_power_state',
      type: 'string'
    },
  ];

  public collectionEvents: object[] = [
    {
      title: 'Сообщение',
      property: 'message',
      class: 'name-start',
      type: 'string',
      icon: 'comment'
    },
    {
      title: 'Cоздатель',
      property: 'user',
      type: 'string',
      class: 'name-end',
      sort: true
    },
    {
      title: 'Дата создания',
      property: 'created',
      type: 'time',
      class: 'name-end',
      sort: true
    }
  ];

  public collectionBackups: object[] = [
    {
      title: 'Название',
      property: 'filename',
      class: 'name-start',
      type: 'string',
      icon: 'file-archive'
    },
    {
      title: 'Пул данных',
      property: 'datapool',
      property_lv2: 'verbose_name',
      type: 'string'
    },
    {
      title: 'Тип',
      property: 'assignment_type',
      type: 'string'
    },
    {
      title: 'Размер (Байт)',
      property: 'size',
      type: 'string'
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string'
    },
  ];

  constructor(
    public dialog: MatDialog,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private service: PoolDetailsService
  ) {}


  public addUser() {
    this.dialog.open(AddUserVmComponent, {
 			disableClose: true,
      width: '500px',
      data: this.data
    });
  }

  public removeUser() {
    this.dialog.open(RemoveUserVmComponent, {
 			disableClose: true,
      width: '500px',
      data: this.data
    });
  }

  public test(): void {
    this.testing = true;
    this.service.testDomainVm(
        this.data.vm.id
      )
      .subscribe((data) => {
        if (data) {
          setTimeout(() => {
            this.testing = false;
            this.tested = true;
            this.connected = data.data.testDomainVm.ok;
          }, 1000);

          setTimeout(() => {
            this.tested = false;
          }, 5000);
        } else {
          this.testing = false;
          this.tested = false;
        }
      });
  }

  public routeTo(route: string): void {
    this.menuActive = route;
  }

  public action(type) {
    if (type == 'start') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: "Подтверждение действия",
            question: "Включить ВМ?",
            button: "Выполнить"
          },
          request: {
            service: this.service,
            action: 'startVm',
            body: {
              vm_id: this.data.vm.id
            }
          }
        }
      })
    }

    if (type == 'suspend') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: "Подтверждение действия",
            question: "Приостановить ВМ?",
            button: "Выполнить"
          },
          request: {
            service: this.service,
            action: 'suspendVm',
            body: {
              vm_id: this.data.vm.id
            }
          }
        }
      })
    }

    if (type == 'shutdown') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: "Подтверждение действия",
            question: "Выключить ВМ?",
            button: "Выполнить"
          },
          request: {
            service: this.service,
            action: 'shutdownVm',
            body: {
              vm_id: this.data.vm.id,
              force: false
            }
          }
        }
      })
    }

    if (type == 'reboot') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: "Подтверждение действия",
            question: "Перезагрузить ВМ?",
            button: "Выполнить"
          },
          request: {
            service: this.service,
            action: 'rebootVm',
            body: {
              vm_id: this.data.vm.id,
              force: false
            }
          }
        }
      })
    }

    if (type == 'shutdown-force') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: "Подтверждение действия",
            question: "Отключить питание ВМ?",
            button: "Выполнить"
          },
          request: {
            service: this.service,
            action: 'shutdownVm',
            body: {
              vm_id: this.data.vm.id,
              force: true
            }
          }
        }
      })
    }

    if (type == 'reboot-force') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: "Подтверждение действия",
            question: "Перезагрузить ВМ принудительно?",
            button: "Выполнить"
          },
          request: {
            service: this.service,
            action: 'rebootVm',
            body: {
              vm_id: this.data.vm.id,
              force: true
            }
          }
        }
      })
    }

    if (type == 'backup') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: "Подтверждение действия",
            question: "Создать резервную копию ВМ?",
            button: "Выполнить"
          },
          request: {
            service: this.service,
            action: 'backupVm',
            body: {
              vm_id: this.data.vm.id,
              force: true
            }
          }
        }
      })
    }
  }

  public prepareVM() {
    if (this.data.typePool == 'automated') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: "Подтверждение действия",
            question: `Подготовить ВМ ${this.data.vm.verbose_name}?`,
            button: "Выполнить"
          },
          request: {
            service: this.service,
            action: 'prepareVm',
            body: {
              vm: this.data.vm.id
            }
          }
        }
      })
    }
  }

  public toPage(message: any): void {
    this.offset = message.offset;
    this.service.getPool(this.data.idPool, this.data.typePool, this.offset).refetch();
  }
}
