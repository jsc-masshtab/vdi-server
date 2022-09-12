import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialog } from '@angular/material/dialog';
import { DomSanitizer } from '@angular/platform-browser';

import { WaitService } from '@core/components/wait/wait.service';

import { YesNoFormComponent } from '@shared/forms-dinamic/yes-no-form/yes-no-form.component';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';


import { InfoEventComponent } from '../../../log/events/info-event/info-event.component';
import { AddUserVmComponent } from './add-user/add-user.component';
import { AddVmConnectionComponent } from './add-vm-connection/add-vm-connection.component';
import { VmCollections } from './collections';
import { ConvertToTemaplteComponent } from './convert-to-template/convert-to-template.component';
import { InfoBackupComponent } from './info-backup/info-backup.component';
import { RemoveUserVmComponent } from './remove-user/remove-user.component';
import { VmDetailsPopupService } from './vm-details-popup.service';

interface Backup {
  backup: {
    filename: string
  };
}

@Component({
  selector: 'vdi-details-popup',
  templateUrl: './vm-details-popup.component.html',
  styleUrls: ['./vm-details-popup.scss']
})

export class VmDetalsPopupComponent extends VmCollections implements OnInit, OnDestroy {

  private sub: Subscription;

  public show: boolean = false;

  public menuActive: string = 'info';

  public testing: boolean = false;
  public tested: boolean = false;
  public connected: boolean = false;
  
  public vnc: any;
  public spice: any;

  public limit = 100;
  public offset = 0;

  vm_status = new FormControl(false);

  constructor(
    public dialog: MatDialog,
    private sanitizer: DomSanitizer,
    private waitService: WaitService,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private service: VmDetailsPopupService
  ) {
    super();
    this.waitService.setWait(true);
  }

  ngOnInit(): void {
    this.refresh();
  }

  public tableActions(action): void {
    this[action.name](action.item);
  }

  public refresh(): void {
    this.show = false;
    this.waitService.setWait(true);

    if (this.sub) {
      this.sub.unsubscribe();
    }

    this.sub = this.service.getVm(this.data.idPool, this.data.vmActive, this.data.controller_id)
    .valueChanges.pipe(map((data: any) => data.data['pool']))
    .subscribe((res) => {

      this.data = { ...this.data, vm: res.vm }

      this.service.updateEntity(this.data);
      
      this.show = true;
      this.waitService.setWait(false);

      if (this.data.vm.status === 'RESERVED') {
        this.vm_status.setValue(true);
      } else {
        this.vm_status.setValue(false);
      }
    });
  }

  public routeTo(route: string): void {

    this.offset = 0;

    if (route === 'vnc') {
      this.show = false;
      this.waitService.setWait(true);

      this.service.getVnc().result().then((res) => {

        if (res.data.pool.vm.vnc_connection) {
          
          const vnc: any = res.data.pool.vm.vnc_connection
          const prot = window.location.protocol;

          let port = 80;

          if (prot === 'https:') {
            port = 443;
          }

          if (vnc.port) {
            port = vnc.port;
          }

          this.vnc = this.sanitizer.bypassSecurityTrustResourceUrl(`novnc/vnc.html?host=${vnc.host}&port=${port}&password=${vnc.password}&path=websockify?token=${vnc.token}`);
        }

        this.show = true;
        this.waitService.setWait(false)
      });
    }

    if (route === 'spice') {
      this.show = false;
      this.waitService.setWait(true)

      this.service.getSpice().result().then((res) => {
        if (res.data.pool.vm.spice_connection) {
          const spice: any = res.data.pool.vm.spice_connection
          this.spice = this.sanitizer.bypassSecurityTrustResourceUrl(spice.connection_url);
        }

        this.show = true;
        this.waitService.setWait(false)
      });
    }

    this.menuActive = route;
  }

  /* Info */

  public test(): void {

    this.testing = true;

    this.service.testDomainVm(this.data.vm.id).subscribe((data: any) => {

      if (data.data) {
        setTimeout(() => {
          this.testing = false;
          this.tested = true;
          this.connected = data.data.testDomainVm.ok;
        }, 1000);

        setTimeout(() => {
          this.tested = false;
        }, 5000);
      }
    
      if (data.errors) {
        this.testing = false;
        this.tested = false;
      }
    }, () => {
      this.testing = false;
      this.tested = false;
    });
  }

  public action(type): void {
    if (type === 'start') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: 'Подтверждение действия',
            question: 'Включить ВМ?',
            button: 'Выполнить'
          },
          request: {
            service: this.service,
            action: 'startVm',
            body: {
              vm_id: this.data.vm.id
            }
          },
          update: {
            method: 'getVm',
            refetch: true
          }
        }
      });
    }

    if (type === 'suspend') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: 'Подтверждение действия',
            question: 'Приостановить ВМ?',
            button: 'Выполнить'
          },
          request: {
            service: this.service,
            action: 'suspendVm',
            body: {
              vm_id: this.data.vm.id
            }
          },
          update: {
            method: 'getVm',
            refetch: true
          }
        }
      });
    }

    if (type === 'shutdown') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: 'Подтверждение действия',
            question: 'Выключить ВМ?',
            button: 'Выполнить'
          },
          request: {
            service: this.service,
            action: 'shutdownVm',
            body: {
              vm_id: this.data.vm.id,
              force: false
            }
          },
          update: {
            method: 'getVm',
            refetch: true
          }
        }
      });
    }

    if (type === 'reboot') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: 'Подтверждение действия',
            question: 'Перезагрузить ВМ?',
            button: 'Выполнить'
          },
          request: {
            service: this.service,
            action: 'rebootVm',
            body: {
              vm_id: this.data.vm.id,
              force: false
            }
          },
          update: {
            method: 'getVm',
            refetch: true
          }
        }
      });
    }

    if (type === 'shutdown-force') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: 'Подтверждение действия',
            question: 'Отключить питание ВМ?',
            button: 'Выполнить'
          },
          request: {
            service: this.service,
            action: 'shutdownVm',
            body: {
              vm_id: this.data.vm.id,
              force: true
            }
          },
          update: {
            method: 'getVm',
            refetch: true
          }
        }
      });
    }

    if (type === 'reboot-force') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: 'Подтверждение действия',
            question: 'Перезагрузить ВМ принудительно?',
            button: 'Выполнить'
          },
          request: {
            service: this.service,
            action: 'rebootVm',
            body: {
              vm_id: this.data.vm.id,
              force: true
            }
          },
          update: {
            method: 'getVm',
            refetch: true
          }
        }
      });
    }

    if (type === 'backup') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: 'Подтверждение действия',
            question: 'Создать резервную копию ВМ?',
            button: 'Выполнить'
          },
          request: {
            service: this.service,
            action: 'backupVm',
            body: {
              vm_id: this.data.vm.id,
              force: true
            }
          },
          update: {
            method: 'getVm',
            refetch: true
          }
        }
      });
    }
  }

  public prepareVM(): void {
    if (this.data.typePool === 'automated' || this.data.typePool === 'guest') {
      this.dialog.open(YesNoFormComponent, {
        disableClose: true,
        width: '500px',
        data: {
          form: {
            header: 'Подтверждение действия',
            question: `Подготовить ВМ ${this.data.vm.verbose_name}?`,
            button: 'Выполнить'
          },
          request: {
            service: this.service,
            action: 'prepareVm',
            body: {
              vm: this.data.vm.id
            }
          },
          update: {
            method: 'getVm',
            refetch: true
          }
        }
      });
    }
  }

  public attachVeilUtils(): void {
    this.dialog.open(YesNoFormComponent, {
      disableClose: true,
      width: '500px',
      data: {
        form: {
          header: 'Подтверждение действия',
          question: `Монтировать образ VeiL utils для ВМ ${this.data.vm.verbose_name}?`,
          button: 'Выполнить'
        },
        request: {
          service: this.service,
          action: 'attachVeilUtils',
          body: {
            id: this.data.vm.id,
            controller_id: this.data.vm.controller.id
          }
        },
        update: {
          method: 'getVm',
          refetch: true
        }
      }
    });
  }

  public changeTemplate(): void {
    this.dialog.open(YesNoFormComponent, {
      disableClose: true,
      width: '500px',
      data: {
        form: {
          header: 'Подтверждение действия',
          question: `Перенести настройки тонкого клона ${this.data.vm.verbose_name} в шаблон ${this.data.vm.parent_name}?`,
          error: 'Внесенные в шаблон настройки применятся ко всем клонам',
          button: 'Выполнить'
        },
        request: {
          service: this.service,
          action: 'changeTemplate',
          body: {
            id: this.data.vm.id,
            controller_id: this.data.vm.controller.id
          }
        },
        update: {
          method: 'getVm',
          refetch: true
        }
      }
    });
  }

  public convertToTemplate(): void {

    this.dialog.open(ConvertToTemaplteComponent, {
      disableClose: true,
      width: '500px',
      data: {
        vm_id: this.data.vm.id,
        controller_id: this.data.vm.controller.id,
        pool: this.data
      }
    });
  }

  public toggleReserve(e): void {

    e.preventDefault();

    if (this.data.vm.status === 'RESERVED') {
      this.activateVm();
    } else {
      this.reserveVm();
    }
  }

  public reserveVm(): void {
    this.dialog.open(YesNoFormComponent, {
      disableClose: true,
      width: '500px',
      data: {
        form: {
          header: 'Подтверждение действия',
          question: `Перевести ВМ ${this.data.vm.verbose_name} в статус "зарезервировано"?`,
          button: 'Выполнить'
        },
        request: {
          service: this.service,
          action: 'reserveVm',
          body: {
            vm_id: this.data.vm.id,
            reserve: true,
          }
        },
        update: {
          method: 'getVm',
          refetch: true
        }
      }
    });
  }

  public activateVm(): void {
    this.dialog.open(YesNoFormComponent, {
      disableClose: true,
      width: '500px',
      data: {
        form: {
          header: 'Подтверждение действия',
          question: `Активировать ВМ ${this.data.vm.verbose_name}?`,
          button: 'Выполнить'
        },
        request: {
          service: this.service,
          action: 'reserveVm',
          body: {
            vm_id: this.data.vm.id,
            reserve: false,
          }
        },
        update: {
          method: 'getVm',
          refetch: true
        }
      }
    });
  }

  /* Connections */

  public addVmConnection(): void {
    this.dialog.open(AddVmConnectionComponent, {
      disableClose: true,
      width: '500px',
      data: this.data
    });
  }

  public removeVmConnection(item: any): void {
    this.dialog.open(YesNoFormComponent, {
      disableClose: true,
      width: '500px',
      data: {
        form: {
          header: 'Подтверждение действия',
          question: `Удалить адрес подключения для ${item.connection_type}?`,
          button: 'Выполнить'
        },
        request: {
          service: this.service,
          action: 'removeVmConnectionData',
          body: {
            id: item.id
          }
        },
        update: {
          method: 'getVm',
          refetch: true
        }
      }
    });
  }

  public openEditConnections(e): void {
    console.log(e)
  }

  public toConnectionPage(message: any): void {
    this.offset = message.offset;
    this.service.getVm(this.data.idPool, this.data.vmActive, this.data.controller_id, this.offset).refetch();
  }

  /* Users */

  public addUser(): void {
    this.dialog.open(AddUserVmComponent, {
      disableClose: true,
      width: '500px',
      data: this.data
    });
  }

  public removeUser(): void {
    this.dialog.open(RemoveUserVmComponent, {
      disableClose: true,
      width: '500px',
      data: this.data
    });
  }
  
  /* Backups */

  public openBackupDetails(backup: Backup): void {
    this.dialog.open(InfoBackupComponent, {
      disableClose: true,
      data: {
        backup
      }
    });
  }
  
  /* Events */

  public openEventDetails(event: Event): void {
    this.dialog.open(InfoEventComponent, {
      disableClose: true,
      data: {
        event
      }
    });
  }
  
  public toEventsPage(message: any): void {
    this.offset = message.offset;
    this.service.getVm(this.data.idPool, this.data.vmActive, this.data.controller_id, this.offset).refetch();
  }

  ngOnDestroy(): void {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }
}
