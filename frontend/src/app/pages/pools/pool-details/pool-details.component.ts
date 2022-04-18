import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute, ParamMap, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';

import { FormForEditComponent } from '@shared/forms-dinamic/change-form/form-edit.component';
import { YesNoFormComponent } from '@shared/forms-dinamic/yes-no-form/yes-no-form.component';

import { AddGropComponent } from './add-group/add-group.component';
import { AddUsersPoolComponent } from './add-users/add-users.component';
import { AddVMStaticPoolComponent } from './add-vms/add-vms.component';
import { IPool, IPoolVms } from './definitions/pool';
import { PoolDetailsService } from './pool-details.service';
import { RemoveGroupComponent } from './remove-group/remove-group.component';
import { RemovePoolComponent } from './remove-pool/remove-pool.component';
import { RemoveUsersPoolComponent } from './remove-users/remove-users.component';
import { RemoveVMStaticPoolComponent } from './remove-vms/remove-vms.component';
import { VmDetalsPopupComponent } from './vm-details-popup/vm-details-popup.component';
import { PoolAddComponent } from '../add-pool/add-pool.component';
import { VmActionComponent } from './vm-action/vm-action.component';
import { PoolCollections } from './collections';

@Component({
  selector: 'vdi-pool-details',
  templateUrl: './pool-details.component.html'
})

export class PoolDetailsComponent extends PoolCollections implements OnInit, OnDestroy {

  public host: boolean = false;
  public poolSettings;
  public user_power_state = new FormControl('all');

  public pool: IPool;

  private idPool: string;
  public  typePool: string;
  public  menuActive: string = 'info';
  private sub_ws_create_pool: Subscription;

  public eventCreatedVm: object[] = [];
  private subPool: Subscription;

  constructor(
    private activatedRoute: ActivatedRoute,
    private router: Router,
    private poolService: PoolDetailsService,
    public dialog: MatDialog
  ){
    super();
  }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      
      this.typePool = param.get('type');
      this.idPool = param.get('id');

      if (this.sub_ws_create_pool) {
        this.sub_ws_create_pool.unsubscribe();
        this.eventCreatedVm = []; // т.к. при переходе на другой из списка,компонент  doesn't destroy
        this.menuActive = 'info'; // у стат. пула нет 'event-vm'
      }

      this.getPool();

      this.user_power_state.valueChanges.subscribe(() => {
        this.getPool();
      });
    });
  }

  routeTo(route: string): void {
    this.menuActive = route;
  }

  close(): void {
    this.router.navigateByUrl('pages/pools');
  }

  sortVms(param) {
    let output_param = param.nameSort;
    this.poolService.orderingVms.nameSort = output_param;
    this.poolService.getPool(this.idPool).refetch().then(data => {
      this.pool = data.data['pool'];
    });
  }

  sortUsers(param) {
    let output_param = param.nameSort;
    this.poolService.orderingUsers.nameSort = output_param;
    this.poolService.getPool(this.idPool).refetch().then(data => {
      this.pool = data.data['pool'];
    });
  }

  sortGroups(param) {
    let output_param = param.nameSort;
    this.poolService.orderingGroups.nameSort = output_param;
    this.poolService.getPool(this.idPool).refetch().then(data => {
      this.pool = data.data['pool'];
    });
  }

  public getPool(): void {
    if (this.subPool) {
      this.subPool.unsubscribe();
    }

    const queryset = {
      user_power_state: this.user_power_state.value
    };

    if (this.user_power_state.value === false) {
      delete queryset['user_power_state'];
    }

    this.host = false;
    this.subPool = this.poolService.getPool(this.idPool)
      .valueChanges.pipe(map((data: any) => data.data['pool']))
      .subscribe((data) => {
        this.pool = data;

        this.host = true;
      },
      () => {
        this.host = true;
      });
  }

  public removePool(): void {
    this.dialog.open(RemovePoolComponent, {
      disableClose: true,
      width: '500px',
      data: {
        idPool: this.idPool,
        namePool: this.pool.verbose_name,
        typePool: this.typePool
      }
    });
  }

  public clearPool(): void {
    this.dialog.open(YesNoFormComponent, {
      disableClose: true,
      width: '500px',
      data: {
        form: {
          header: 'Сброс ошибок',
          question: `Сбросить все ошибки пула ${this.pool.verbose_name}?`,
          button: 'Выполнить'
        },
        request: {
          service: this.poolService,
          action: 'clearPool',
          body: {
            pool_id: this.idPool,
          }
        }
      }
    });
  }

  public addUsers(): void {
    this.dialog.open(AddUsersPoolComponent, {
      disableClose: true,
      width: '500px',
      data: {
        idPool: this.idPool,
        namePool: this.pool.verbose_name,
        typePool: this.typePool
      }
    });
  }

  public removeUsers(): void {
    this.dialog.open(RemoveUsersPoolComponent, {
      disableClose: true,
      width: '500px',
      data: {
        idPool: this.idPool,
        namePool: this.pool.verbose_name,
        typePool: this.typePool
      }
    });
  }

  public addVM(): void {
    this.dialog.open(AddVMStaticPoolComponent, {
      disableClose: true,
      width: '500px',
      data: {
        idPool: this.idPool,
        namePool: this.pool.verbose_name,
        idResourcePool: this.pool.resource_pool_id,
        idController: this.pool.controller.id,
        typePool: this.typePool
      }
    });
  }

  public removeVM(): void {
    this.dialog.open(RemoveVMStaticPoolComponent, {
      disableClose: true,
      width: '500px',
      data: {
        idPool: this.idPool,
        namePool: this.pool.verbose_name,
        vms: this.pool.vms,
        typePool: this.typePool
      }
    });
  }

  public backupVms(): void {
    this.dialog.open(YesNoFormComponent, {
      disableClose: true,
      width: '500px',
      data: {
        form: {
          header: 'Подтверждение действия',
          question: 'Создать резервные копии всех виртуальных машин пула?',
          button: 'Выполнить'
        },
        request: {
          service: this.poolService,
          action: 'backupVms',
          body: {
            pool_id: this.idPool
          }
        }
      }
    });
  }

  public clickVm(vmActive: IPoolVms): void  {
    this.dialog.open(VmDetalsPopupComponent, {
      disableClose: true,
      width: '99vw',
      height: '99vh',
      maxHeight: '980px',
      maxWidth: '1400px',
      data: {
        typePool: this.typePool,
        usersPool: this.pool.users,
        idPool: this.idPool,
        username: vmActive.user.username,
        controller_id: this.pool.controller.id,
        vmActive: vmActive.id,
        vms: vmActive
      }
    });
  }

  public actionEdit(method) {
    this[method]();
  }

  public expandPool(): void {
    this.dialog.open(YesNoFormComponent, {
      disableClose: true,
      width: '500px',
      data: {
        form: {
          header: 'Подтверждение действия',
          question: 'Расширить пул?',
          button: 'Выполнить'
        },
        request: {
          service: this.poolService,
          action: 'expandPool',
          body: {
            pool_id: this.idPool
          }
        }
      }
    });
  }

  public changeName(): void {
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.poolService,
          method: 'updatePool',
          params: {
            pool_id: this.idPool,
            pool_type: this.typePool
          }
        },
        settings: {
          entity: 'pool-details',
          header: 'Изменение имени пула',
          buttonAction: 'Изменить',
          form: [{
            tag: 'input',
            type: 'text',
            fieldName: 'verbose_name',
            fieldValue: this.pool.verbose_name,
          }]
        },
        update: {
          method: 'getPool',
          refetch: true,
          params: [
            this.idPool,
            this.typePool
          ],
        }
      }
    });
  }

  public changeConnectionType(): void {
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.poolService,
          method: 'updatePool',
          params: {
            pool_id: this.idPool,
            pool_type: this.typePool
          }
        },
        settings: {
          entity: 'pool-details',
          header: 'Изменение типа подключения пула',
          buttonAction: 'Изменить',
          form: [{
            tag: 'select',
            multiple: true,
            title: 'Выбрать тип подключения',
            fieldName: 'connection_types',
            data: this.typePool === 'rds' ? ['RDP', 'NATIVE_RDP'] : ['RDP', 'NATIVE_RDP', 'SPICE', 'SPICE_DIRECT', 'X2GO'],
            fieldValue: this.pool.assigned_connection_types,
          }]
        },
        update: {
          method: 'getPool',
          refetch: true,
          params: [
            this.idPool,
            this.typePool
          ],
        }
      }
    });
  }

  public changeMaxAutomatedPool(): void {
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.poolService,
          method: 'updatePool',
          params: {
            pool_id: this.idPool,
            pool_type: this.typePool
          }
        },
        settings: {
          entity: 'pool-details',
          header: 'Изменение максимального количества создаваемых ВМ',
          buttonAction: 'Изменить',
          form: [{
            tag: 'input',
            type: 'number',
            fieldName: 'total_size',
            fieldValue: this.pool.total_size,
          }]
        },
        update: {
          method: 'getPool',
          refetch: true,
          params: [
            this.idPool,
            this.typePool
          ]
        }
      }
    });
  }

  public changeAutomatedPoolIncreaseStep(): void {
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.poolService,
          method: 'updatePool',
          params: {
            pool_id: this.idPool,
            pool_type: this.typePool
          }
        },
        settings: {
          entity: 'pool-details',
          header: 'Изменение шага расширения пула',
          buttonAction: 'Изменить',
          form: [{
            tag: 'input',
            type: 'number',
            fieldName: 'increase_step',
            fieldValue: this.pool.increase_step,
          }]
        },
        update: {
          method: 'getPool',
          refetch: true,
          params: [
            this.idPool,
            this.typePool
          ]
        }
      }
    });
  }

  public changeAutomatedPoolReserveSize(): void {
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.poolService,
          method: 'updatePool',
          params: {
            pool_id: this.idPool,
            pool_type: this.typePool
          }
        },
        settings: {
          entity: 'pool-details',
          header: 'Изменение порогового количества свободных ВМ',
          buttonAction: 'Изменить',
          form: [{
            tag: 'input',
            type: 'number',
            fieldName: 'reserve_size',
            fieldValue: this.pool.reserve_size,
          }]
        },
        update: {
          method: 'getPool',
          refetch: true,
          params: [
            this.idPool,
            this.typePool
          ]
        }
      }
    });
  }

  public changeGuestPoolWaitingTime(): void {
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.poolService,
          method: 'updatePool',
          params: {
            pool_id: this.idPool,
            pool_type: this.typePool
          }
        },
        settings: {
          entity: 'pool-details',
          header: 'Изменение времени жизни ВМ после потери связи (сек)',
          buttonAction: 'Изменить',
          form: [{
            tag: 'input',
            type: 'number',
            fieldName: 'vm_disconnect_action_timeout',
            fieldValue: this.pool.vm_disconnect_action_timeout,
          }]
        },
        update: {
          method: 'getPool',
          refetch: true,
          params: [
            this.idPool,
            this.typePool
          ]
        }
      }
    });
  }

  public changeTemplateForVmAutomatedPool(): void {
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.poolService,
          method: 'updatePool',
          params: {
            pool_id: this.idPool,
            pool_type: this.typePool
          }
        },
        settings: {
          entity: 'pool-details',
          header: 'Изменение шаблона для ВМ',
          buttonAction: 'Изменить',
          danger: 'Произойдет переименование ВМ и переназначение hostname на ECP VeiL!',
          form: [{
            tag: 'input',
            type: 'text',
            fieldName: 'vm_name_template',
            fieldValue: this.pool.vm_name_template,
          }]
        },
        update: {
          method: 'getPool',
          refetch: true,
          params: [
            this.idPool,
            this.typePool
          ]
        }
      }
    });
  }

  public changeAutomatedPoolCreate_thin_clones(): void {
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.poolService,
          method: 'updatePool',
          params: {
            pool_id: this.idPool,
            pool_type: this.typePool
          }
        },
        settings: {
          entity: 'pool-details',
          header: 'Изменение настройки тонких клонов',
          buttonAction: 'Изменить',
          form: [{
            tag: 'input',
            type: 'checkbox',
            fieldName: 'create_thin_clones',
            fieldValue: this.pool.create_thin_clones,
            description: 'Создавать тонкие клоны'
          }]
        },
        update: {
          method: 'getPool',
          refetch: true,
          params: [
            this.idPool,
            this.typePool
          ]
        }
      }
    });
  }

  public changeAutomatedPoolPrepare_vms(): void {
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.poolService,
          method: 'updatePool',
          params: {
            pool_id: this.idPool,
            pool_type: this.typePool
          }
        },
        settings: {
          entity: 'pool-details',
          header: 'Изменение настройки автоматической подготовки ВМ',
          buttonAction: 'Изменить',
          form: [{
            tag: 'input',
            type: 'checkbox',
            fieldName: 'enable_vms_remote_access',
            fieldValue: this.pool.enable_vms_remote_access,
            dependName: {
              on: [], off: ['start_vms', 'set_vms_hostnames', 'include_vms_in_ad']
            },
            description: 'Включать удаленный доступ на ВМ'
          },
          {
            tag: 'input',
            type: 'checkbox',
            fieldName: 'start_vms',
            fieldValue: this.pool.start_vms,
            dependName: {
              on: ['enable_vms_remote_access'], off: ['set_vms_hostnames', 'include_vms_in_ad']
            },
            description: 'Включать ВМ'
          },
          {
            tag: 'input',
            type: 'checkbox',
            fieldName: 'set_vms_hostnames',
            fieldValue: this.pool.set_vms_hostnames,
            dependName: {
              on: ['enable_vms_remote_access', 'start_vms'], off: ['include_vms_in_ad']
            },
            description: 'Задавать hostname ВМ'
          },
          {
            tag: 'input',
            type: 'checkbox',
            fieldName: 'include_vms_in_ad',
            fieldValue: this.pool.include_vms_in_ad,
            dependName: {
              on: ['enable_vms_remote_access', 'start_vms', 'set_vms_hostnames'], off: []
            },
            description: 'Вводить ВМ в домен'
          }]
        },
        update: {
          method: 'getPool',
          refetch: true,
          params: [
            this.idPool,
            this.typePool
          ]
        }
      }
    });
  }

  public changeAutomatedPoolKeep_vms_on(): void {
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.poolService,
          method: 'updatePool',
          params: {
            pool_id: this.idPool,
            pool_type: this.typePool
          }
        },
        settings: {
          entity: 'pool-details',
          header: 'Изменение состояния ВМ',
          buttonAction: 'Изменить',
          form: [{
            tag: 'input',
            type: 'checkbox',
            fieldName: 'keep_vms_on',
            fieldValue: this.pool.keep_vms_on,
            description: 'Держать ВМ с пользователями включенными'
          }]
        },
        update: {
          method: 'getPool',
          refetch: true,
          params: [
            this.idPool,
            this.typePool
          ]
        }
      }
    });
  }

  public changeAdCnPatternForGroupAutomatedPool(): void {
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.poolService,
          method: 'updatePool',
          params: {
            pool_id: this.idPool,
            pool_type: this.typePool
          }
        },
        settings: {
          entity: 'pool-details',
          header: 'Изменение наименования групп для добавления ВМ в AD',
          buttonAction: 'Изменить',
          danger: 'В НОВУЮ группу добавятся только НОВЫЕ виртуальные машины!',
          form: [{
            tag: 'input',
            type: 'text',
            fieldName: 'ad_ou',
            unrequired: true,
            fieldValue: this.pool.ad_ou,
          }]
        },
        update: {
          method: 'getPool',
          refetch: true,
          params: [
            this.idPool,
            this.typePool
          ]
        }
      }
    });
  }

  public manageVm(): void {

    this.dialog.open(VmActionComponent, {
      disableClose: true,
      width: '500px',
      data: {
        freeVm: this.pool.free_vm_from_user,
        action: this.pool.vm_action_upon_user_disconnect,
        timeout: this.pool.vm_disconnect_action_timeout,
        idPool: this.idPool,
        poolType: this.pool.pool_type.toLowerCase(),
      }
    });
  }

  public addGroup() {
    this.dialog.open(AddGropComponent, {
      disableClose: true,
      width: '500px',
      data: {
        id: this.idPool,
        typePool: this.typePool,
        verbose_name: this.pool['verbose_name'],
        groups: this.pool['possible_groups']
      }
    });
  }

  public removeGroup() {
    this.dialog.open(RemoveGroupComponent, {
      disableClose: true,
      width: '500px',
      data: {
        id: this.idPool,
        typePool: this.typePool,
        verbose_name: this.pool['verbose_name'],
        groups: this.pool['assigned_groups']
      }
    });
  }
  
  public copyPool(): void {
    this.poolService.copyPool(this.idPool).subscribe((res) => {
       this.poolSettings = JSON.parse(res.data.copyDynamicPool.pool_settings);

       this.dialog.open(PoolAddComponent, {
         disableClose: true,
         width: '500px',
         data: this.poolSettings
       });
    });

  }

  public converData(): void {
  }

  ngOnDestroy() {
    if (this.sub_ws_create_pool) {
      this.sub_ws_create_pool.unsubscribe();
    }

    if (this.subPool) {
      this.subPool.unsubscribe();
    }
  }
}
