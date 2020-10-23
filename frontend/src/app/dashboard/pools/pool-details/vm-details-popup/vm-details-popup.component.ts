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

  public menuActive: string = 'info';
  public collectionIntoVmAutomated: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string'
    },
    {
      title: 'Шаблон',
      property: 'template',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Пользователь',
      property: 'user',
      property_lv2: 'username'
    },
    {
      title: 'Состояние',
      property: 'power_state',
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
      title: 'Пользователь',
      property: 'user',
      property_lv2: 'username'
    },
    {
      title: 'Состояние',
      property: 'power_state',
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

  public routeTo(route: string): void {
    if (route === 'info') {
      this.menuActive = 'info';
    }
  }

  public action(type) {
    if (type == 'start') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: "Включение ВМ",
            question: "Включить ВМ?",
            button: "Включить"
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

    if (type == 'shutdown') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: "Выключение ВМ",
            question: "Выключить ВМ?",
            button: "Выключить"
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
            header: "Перезагрузка ВМ",
            question: "Перезагрузить ВМ?",
            button: "Перезагрузить"
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
            header: "Отключение питания ВМ",
            question: "Отключить питание ВМ?",
            button: "Отключить"
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
            header: "Горячая перезагрузка ВМ",
            question: "Перезагрузить ВМ принудительно?",
            button: "Перезагрузить"
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
  }

}
