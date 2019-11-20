import { Subscription } from 'rxjs';
import { WebsocketPoolService } from './../../common/classes/websockPool.service';
import { PoolsService } from './../all-pools/pools.service';
import { IPool } from './definitions/pool';
import { VmDetalsPopupComponent } from './vm-details-popup/vm-details-popup.component';
import { RemoveUsersPoolComponent } from './remove-users/remove-users.component';
import { AddUsersPoolComponent } from './add-users/add-users.component';
import { RemoveVMStaticPoolComponent } from './remove-vms/remove-vms.component';
import { AddVMStaticPoolComponent } from './add-vms/add-vms.component';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, ParamMap, Router } from '@angular/router';
import { MatDialog } from '@angular/material';
import { RemovePoolComponent } from './remove-pool/remove-pool.component';
import { PoolDetailsService } from './pool-details.service';
import { FormForEditComponent } from 'src/app/common/forms-dinamic/change-form/form-edit.component';
import { skip, map, filter, catchError } from 'rxjs/operators';
import { of } from 'rxjs';



@Component({
  selector: 'vdi-pool-details',
  templateUrl: './pool-details.component.html'
})


export class PoolDetailsComponent implements OnInit, OnDestroy {

  public host: boolean = false;

  public pool: IPool;
  public collectionDetailsStatic: any[] = [
    {
      title: 'Название',
      property: 'name',
      type: 'string',
      edit: 'changeName'
    },
    {
      title: 'Тип',
      property: 'desktop_pool_type',
      type: 'string'
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'ip'
    },
    {
      title: 'Кластер',
      property: 'pool_resources_names',
      property_lv2: 'cluster_name'
    },
    {
      title: 'Сервер',
      property: 'pool_resources_names',
      property_lv2: 'node_name'
    },
    {
      title: 'Пул данных',
      property: 'pool_resources_names',
      property_lv2: 'datapool_name'
    },
    {
      title: 'Всего ВМ',
      property: 'vms',
      type: 'array-length'
    },
    {
      title: 'Пользователи',
      property: 'users',
      type: {
        propertyDepend: 'username',
        typeDepend: 'propertyInObjectsInArray'
      }
    }
  ];
  public collectionDetailsAutomated: any[] = [
    {
      title: 'Название',
      property: 'name',
      type: 'string',
      edit: 'changeName'
    },
    {
      title: 'Тип',
      property: 'desktop_pool_type',
      type: 'string'
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'ip'
    },
    {
      title: 'Кластер',
      property: 'pool_resources_names',
      property_lv2: 'cluster_name'
    },
    {
      title: 'Сервер',
      property: 'pool_resources_names',
      property_lv2: 'node_name'
    },
    {
      title: 'Пул данных',
      property: 'pool_resources_names',
      property_lv2: 'datapool_name'
    },
    {
      title: 'Начальное количество ВМ',    // всего вм
      property: 'settings',
      property_lv2: 'initial_size'
    },
    {
      title: 'Количество создаваемых ВМ',      // сколько свободных осталось
      property: 'settings',
      property_lv2: 'reserve_size',
      edit: 'changeAutomatedPoolReserveSize'
    },
    {
      title: 'Максимальное количество создаваемых ВМ',
      // Максимальное количество ВМ в пуле -  c тонкого клиента вм будут создаваться
      // с каждым подключ. пользователем даже,если рес-сы закончатся
      property: 'settings',
      property_lv2: 'total_size',
      edit: 'changeMaxAutomatedPool'
    },
    {
      title: 'Создано ВМ',
      property: 'vms',
      type: 'array-length'
    },
    {
      title: 'Шаблон для ВМ',
      property: 'settings',
      property_lv2: 'vm_name_template',
      edit: 'changeTemplateForVmAutomatedPool'
    },
    {
      title: 'Пользователи',
      property: 'users',
      type: {
        propertyDepend: 'username',
        typeDepend: 'propertyInObjectsInArray'
      }
    }
  ];

  public collectionVmsAutomated: any[] = [
    {
      title: 'Название',
      property: 'name',
      class: 'name-start',
      icon: 'desktop',
      type: 'string'
    },
    {
      title: 'Шаблон',
      property: 'template',
      property_lv2: 'name'
    },
    {
      title: 'Пользователь',
      property: 'user',
      property_lv2: 'username'
    },
    {
      title: 'Статус',
      property: 'status'
    }
  ];
  public collectionVmsStatic: any[] = [
    {
      title: 'Название',
      property: 'name',
      class: 'name-start',
      icon: 'desktop',
      type: 'string'
    },
    {
      title: 'Пользователь',
      property: 'user',
      property_lv2: 'username'
    },
    {
      title: 'Статус',
      property: 'status'
    }
  ];

  public collectionUsers: any[] = [
    {
      title: 'Имя пользователя',
      property: 'username',
      class: 'name-start',
      icon: 'user',
      type: 'string'
    }
  ];

  public collectionEventVm: any[] = [
    {
      title: 'Событие',
      property: 'msg',
      class: 'name-start',
      icon: 'comment',
      type: 'string'
    }
  ];

  private idPool: number;
  public  typePool: string;
  public  menuActive: string = 'info';
  private sub_ws_create_pool: Subscription;

  public eventCreatedVm: object[] = [];

  constructor(private activatedRoute: ActivatedRoute,
              private router: Router,
              private poolService: PoolDetailsService,
              private poolsService: PoolsService,
              public  dialog: MatDialog,
              private ws_create_pool_service: WebsocketPoolService) {}

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.typePool = param.get('type');
      this.idPool = +param.get('id');
      if (this.sub_ws_create_pool) {
        this.sub_ws_create_pool.unsubscribe();
        this.eventCreatedVm = []; // т.к. при переходе на другой из списка,компонент  doesn't destroy
        this.menuActive = 'info'; // у стат. пула нет 'event-vm'
      }
      this.getPool();
      this.getMsgCreatePool();
    });
  }

  private getMsgCreatePool(): void {
    this.sub_ws_create_pool = this.ws_create_pool_service.getMsg().pipe(
                                                                  skip(1),
                                                                  map(msg => JSON.parse(msg)),
                                                                  filter((msg: object) => msg['pool_id'] === this.idPool),
                                                                  catchError(() => of('error')) // complete()
                                                                  )
    .subscribe((msg: object | 'error') => {
      if (msg !== 'error') {
        this.eventCreatedVm.push(msg);
      }
    },
    (error) => console.log(error, 'error'),
    () =>  console.log( 'complete'));
  }


  public getPool(): void {
    this.host = false;
    this.poolService.getPool({id: this.idPool, type: this.typePool})
      .subscribe( (data) => {
        this.pool = data;
        this.host = true;
      },
      () => {
        this.host = true;
      });
  }

  public removePool(): void {
    this.dialog.open(RemovePoolComponent, {
      width: '500px',
      data: {
        idPool: this.idPool,
        namePool: this.pool.name
      }
    });
  }

  public addUsers(): void {
    this.dialog.open(AddUsersPoolComponent, {
      width: '500px',
      data: {
        idPool: this.idPool,
        namePool: this.pool.name,
        typePool: this.typePool
      }
    });
  }

  public removeUsers(): void {
    this.dialog.open(RemoveUsersPoolComponent, {
      width: '500px',
      data: {
        idPool: this.idPool,
        namePool: this.pool.name,
        typePool: this.typePool
      }
    });
  }

  public addVM(): void {
    this.dialog.open(AddVMStaticPoolComponent, {
      width: '500px',
      data: {
        idPool: this.idPool,
        namePool: this.pool.name,
        idCluster: this.pool.settings.cluster_id,
        idNode: this.pool.settings.node_id,
        typePool: this.typePool
      }
    });
  }

  public removeVM(): void {
    this.dialog.open(RemoveVMStaticPoolComponent, {
      width: '500px',
      data: {
        idPool: this.idPool,
        namePool: this.pool.name,
        vms: this.pool.vms,
        typePool: this.typePool
      }
    });
  }

  public clickVm(vmActive): void  {
    this.dialog.open(VmDetalsPopupComponent, {
      width: '1000px',
      data: {
        vm: vmActive,
        typePool: this.typePool,
        usersPool: this.pool.users,
        idPool: this.idPool
      }
    });
  }

  public actionEdit(method) {
    this[method]();
  }

// @ts-ignore: Unreachable code error
  private changeName(): void {
    this.dialog.open(FormForEditComponent, {
      width: '500px',
      data: {
        post: {
          service: this.poolService,
          method: 'editNamePool',
          params: {
            id: this.idPool
          }
        },
        settings: {
          entity: 'pool-details',
          header: 'Изменение имени пула',
          buttonAction: 'Изменить',
          form: [{
            tag: 'input',
            type: 'text',
            fieldName: 'name',
            fieldValue: this.pool.name,
          }]
        },
        update: {
          method: 'getPool',
          params: {
            id: this.idPool,
            type: this.typePool
          },
        },
        updateDepend: {
          service: this.poolsService,
          method: 'getAllPools'
        }
      }
    });
  }

  // @ts-ignore: Unreachable code error
  private changeMaxAutomatedPool(): void {
    this.dialog.open(FormForEditComponent, {
      width: '500px',
      data: {
        post: {
          service: this.poolService,
          method: 'changeAutomatedPoolTotalSize',
          params: {
            id: this.idPool
          }
        },
        settings: {
          entity: 'pool-details',
          header: 'Изменение максимального количества создаваемых ВМ',
          buttonAction: 'Изменить',
          form: [{
            tag: 'input',
            type: 'number',
            fieldName: 'new_total_size',
            fieldValue: this.pool.settings.total_size,
          }]
        },
        update: {
          method: 'getPool',
          params: {
            id: this.idPool,
            type: this.typePool
          }
        }
      }
    });
  }

  // @ts-ignore: Unreachable code error
  private changeAutomatedPoolReserveSize(): void {
    this.dialog.open(FormForEditComponent, {
      width: '500px',
      data: {
        post: {
          service: this.poolService,
          method: 'changeAutomatedPoolReserveSize',
          params: {
            id: this.idPool
          }
        },
        settings: {
          entity: 'pool-details',
          header: 'Изменение количества создаваемых ВМ',
          buttonAction: 'Изменить',
          form: [{
            tag: 'input',
            type: 'number',
            fieldName: 'reserve_size',
            fieldValue: this.pool.settings.reserve_size,
          }]
        },
        update: {
          method: 'getPool',
          params: {
            id: this.idPool,
            type: this.typePool
          }
        }
      }
    });
  }

  // @ts-ignore: Unreachable code error
  private changeTemplateForVmAutomatedPool(): void {
    this.dialog.open(FormForEditComponent, {
      width: '500px',
      data: {
        post: {
          service: this.poolService,
          method: 'changeTemplateForVmAutomatedPool',
          params: {
            id: this.idPool
          }
        },
        settings: {
          entity: 'pool-details',
          header: 'Изменение шаблона для ВМ',
          buttonAction: 'Изменить',
          form: [{
            tag: 'input',
            type: 'text',
            fieldName: 'vm_name_template',
            fieldValue: this.pool.settings.vm_name_template,
          }]
        },
        update: {
          method: 'getPool',
          params: {
            id: this.idPool,
            type: this.typePool
          }
        }
      }
    });
  }

  public routeTo(route: string): void {
    if (route === 'info') {
      this.menuActive = 'info';
    }

    if (route === 'vms') {
      this.menuActive = 'vms';
    }

    if (route === 'users') {
      this.menuActive = 'users';
    }

    if (route === 'event-vm') {
      this.menuActive = 'event-vm';
    }
  }

  public close(): void  {
    this.router.navigateByUrl('/pools');
  }

  ngOnDestroy() {
    if (this.sub_ws_create_pool) {
      this.sub_ws_create_pool.unsubscribe();
    }
  }
}
