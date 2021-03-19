import { Subscription } from 'rxjs';
import { IPool, IPoolVms } from './definitions/pool';
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
import { FormForEditComponent } from 'src/app/dashboard/common/forms-dinamic/change-form/form-edit.component';
import { map, take } from 'rxjs/operators';
import { RemoveGroupComponent } from './remove-group/remove-group.component';
import { AddGropComponent } from './add-group/add-group.component';
import { YesNoFormComponent } from '../../common/forms-dinamic/yes-no-form/yes-no-form.component';
import { FormControl } from '@angular/forms';

@Component({
  selector: 'vdi-pool-details',
  templateUrl: './pool-details.component.html'
})

export class PoolDetailsComponent implements OnInit, OnDestroy {

  public host: boolean = false;
  user_power_state = new FormControl('all');

  public pool: IPool;

  public collectionDetailsStatic: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string',
      edit: 'changeName'
    },
    {
      title: 'Тип',
      property: 'pool_type',
      type: 'string'
    },
    {
      title: 'Тип подключения пула',
      property: 'assigned_connection_types',
      type: 'string',
      edit: 'changeConnectionType'
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Адрес контроллера',
      property: 'controller',
      property_lv2: 'address'
    },
    {
      title: 'Пул ресурсов',
      property: 'resource_pool',
      property_lv2: 'verbose_name',
    },
    {
      title: 'Всего ВМ',
      property: 'vms',
      type: 'array-length'
    },
    {
      title: 'Пользователи',
      property: 'users',
      type: 'array-length'
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string'
    }
  ];

  public collectionDetailsAutomated: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string',
      edit: 'changeName'
    },
    {
      title: 'Тип',
      property: 'pool_type',
      type: 'string'
    },
    {
      title: 'Тип подключения пула',
      property: 'assigned_connection_types',
      type: 'string',
      edit: 'changeConnectionType'
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Адрес контроллера',
      property: 'controller',
      property_lv2: 'address'
    },
    {
      title: 'Тонкие клоны',
      property: 'create_thin_clones',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Создаются', 'Не создаются']
      },
      edit: 'changeAutomatedPoolCreate_thin_clones'
    },
    {
      title: 'Подготавливать ВМ',
      property: 'prepare_vms',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Да', 'Нет']
      },
      edit: 'changeAutomatedPoolPrepare_vms'
    },
    {
      title: 'Держать ВМ с пользователями включенными',
      property: 'keep_vms_on',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Да', 'Нет']
      },
      edit: 'changeAutomatedPoolKeep_vms_on'
    },
    {
      title: 'Пул ресурсов',
      property: 'resource_pool',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Начальное количество ВМ',
      property: 'initial_size',
      type: 'string'
    },
    {
      title: 'Шаг расширения пула',
      property: 'increase_step',
      type: 'string',
      edit: 'changeAutomatedPoolIncreaseStep'
    },
    {
      title: 'Максимальное количество создаваемых ВМ',
      // Максимальное количество ВМ в пуле -  c тонкого клиента вм будут создаваться
      // с каждым подключ. пользователем даже,если рес-сы закончатся
      property: 'total_size',
      type: 'string',
      edit: 'changeMaxAutomatedPool'
    },
    {
      title: 'Пороговое количество свободных ВМ',
      property: 'reserve_size',
      type: 'string',
      edit: 'changeAutomatedPoolReserveSize'
    },
    {
      title: 'Количество доступных ВМ',
      property: 'vms',
      type: 'array-length'
    },
    {
      title: 'Шаблон ВМ',
      property: 'template',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Шаблон для имени ВМ',
      property: 'vm_name_template',
      type: 'string',
      edit: 'changeTemplateForVmAutomatedPool'
    },
    {
      title: 'Наименование групп для добавления ВМ в AD',
      property: 'ad_cn_pattern',
      type: 'string',
      edit: 'changeAdCnPatternForGroupAutomatedPool'
    },
    {
      title: 'Пользователи',
      property: 'users',
      type: 'array-length'
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string'
    }
  ];

  public collectionVmsAutomated: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'desktop',
      type: 'string'
    },
    {
      title: 'Шаблон',
      property: 'template',
      property_lv2: 'verbose_name'
    },
    // {
    //   title: 'Принадлежность',
    //   property: 'in_domain',
    //   type: {
    //     typeDepend: 'boolean',
    //     propertyDepend: ['В домене', 'Не в домене']
    //   }
    // },
    {
      title: 'Пользователь',
      property: 'user',
      property_lv2: 'username'
    },
    {
      title: 'Статус',
      property: 'status'
    },
    {
      title: 'Гостевой агент',
      property: 'qemu_state',
      type: 'string'
    }
  ];

  public collectionVmsStatic: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'desktop',
      type: 'string'
    },
    // {
    //   title: 'Принадлежность',
    //   property: 'in_domain',
    //   type: {
    //     typeDepend: 'boolean',
    //     propertyDepend: ['В домене', 'Не в домене']
    //   }
    // },
    {
      title: 'Пользователь',
      property: 'user',
      property_lv2: 'username'
    },
    {
      title: 'Статус',
      property: 'status'
    },
    {
      title: 'Гостевой агент',
      property: 'qemu_state',
      type: 'string'
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

  public collectionGroups: object[] = [
    {
      title: 'Название группы',
      type: 'string',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'users-cog'
    }
  ];

  private idPool: string;
  public  typePool: string;
  public  menuActive: string = 'info';
  private sub_ws_create_pool: Subscription;

  public eventCreatedVm: object[] = [];
  private subPool: Subscription;

  constructor(private activatedRoute: ActivatedRoute,
              private router: Router,
              private poolService: PoolDetailsService,
              public  dialog: MatDialog) {}

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
      // this.getMsgCreatePool();
      this.user_power_state.valueChanges.subscribe(() => {
        this.getPool();
      });
    });
  }

  // private getMsgCreatePool(): void {
  //   this.sub_ws_create_pool = this.ws.getMsgCreateVMPoll().pipe(
  //                                                                 skip(1),
  //                                                                 map(msg => JSON.parse(msg)),
  //                                                                 filter((msg: object) => msg['pool_id'] === this.idPool),
  //                                                                 catchError(() => of('error')) // complete()
  //                                                                 )
  //   .subscribe((msg: object | 'error') => {
  //     if (msg !== 'error') {
  //       this.eventCreatedVm.push(msg);
  //     }
  //   },
  //   (error) => console.log(error, 'error'),
  //   () =>  console.log( 'complete'));
  // }

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
    this.subPool = this.poolService.getPool(this.idPool, this.typePool)
      .valueChanges.pipe(map((data: any) => data.data['pool']))
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

  // public prepareVM(): void {
  //   this.dialog.open(PrepareVmPoolComponent, {
  //     disableClose: true,
  //     width: '500px',
  //     data: {
  //       idPool: this.idPool,
  //       namePool: this.pool.verbose_name,
  //       idCluster: this.pool.cluster_id,
  //       idNode: this.pool.node_id,
  //       idController: this.pool.controller.id,
  //       vms: this.pool.vms,
  //       typePool: this.typePool
  //     }
  //   });
  // }

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
    this.poolService.getVm(this.idPool, vmActive.id, this.pool.controller.id).valueChanges.pipe(take(1)).subscribe((res) => {
      this.dialog.open(VmDetalsPopupComponent, {
        disableClose: true,
        width: '1000px',
        data: {
          vm: res.data.pool.vm,
          typePool: this.typePool,
          usersPool: this.pool.users,
          idPool: this.idPool,
          username: vmActive.user.username,
          vms: vmActive
        }
      });
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

// @ts-ignore: Unreachable code error
  private changeName(): void {
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

  // @ts-ignore: Unreachable code error
  private changeConnectionType(): void {
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
            data: ['RDP', 'NATIVE_RDP', 'SPICE', 'SPICE_DIRECT'],
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

  // @ts-ignore: Unreachable code error
  private changeMaxAutomatedPool(): void {
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

  // @ts-ignore: Unreachable code error
  private changeAutomatedPoolIncreaseStep(): void {
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

   // @ts-ignore: Unreachable code error
  private changeAutomatedPoolReserveSize(): void {
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

  // @ts-ignore: Unreachable code error
  private changeTemplateForVmAutomatedPool(): void {
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

  // @ts-ignore: Unreachable code error
  private changeAutomatedPoolCreate_thin_clones(): void {
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

  // @ts-ignore: Unreachable code error
  private changeAutomatedPoolPrepare_vms(): void {
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
            fieldName: 'prepare_vms',
            fieldValue: this.pool.prepare_vms,
            description: 'Подготавливать ВМ'
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

  // @ts-ignore: Unreachable code error
  private changeAutomatedPoolKeep_vms_on(): void {
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

  // @ts-ignore: Unreachable code error
  private changeAdCnPatternForGroupAutomatedPool(): void {
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
            fieldName: 'ad_cn_pattern',
            fieldValue: this.pool.ad_cn_pattern,
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

  public routeTo(route: string): void {
    this.menuActive = route;
  }

  public close(): void  {
    this.router.navigateByUrl('pages/pools');
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

  ngOnDestroy() {
    if (this.sub_ws_create_pool) {
      this.sub_ws_create_pool.unsubscribe();
    }

    if (this.subPool) {
      this.subPool.unsubscribe();
    }
  }
}
