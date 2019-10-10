import { IPool } from './definitions/pool';
import { VmDetalsPopupComponent } from './vm-details-popup/vm-details-popup.component';
import { RemoveUsersPoolComponent } from './remove-users/remove-users.component';
import { AddUsersPoolComponent } from './add-users/add-users.component';
import { RemoveVMStaticPoolComponent } from './remove-vms/remove-vms.component';
import { AddVMStaticPoolComponent } from './add-vms/add-vms.component';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, ParamMap, Router } from '@angular/router';
import { MatDialog } from '@angular/material';
import { RemovePoolComponent } from './remove-pool/remove-pool.component';
import { PoolDetailsService } from './pool-details.service';
import { FormForEditComponent } from 'src/app/common/components/shared/change-form/form-edit.component';



@Component({
  selector: 'vdi-pool-details',
  templateUrl: './pool-details.component.html'
})


export class PoolDetailsComponent implements OnInit {

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
      type: 'string'
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
      property_lv2: 'reserve_size'
    },
    {
      title: 'Максимальное количество создаваемых ВМ',
      // Максимальное количество ВМ в пуле -  c тонкого клиента вм будут создаваться
      // с каждым подключ. пользователем даже,если рес-сы закончатся
      property: 'settings',
      property_lv2: 'total_size'
    },
    {
      title: 'Создано ВМ',
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

  public collectionVmsAutomated: any[] = [
    {
      title: '№',
      property: 'index'
    },
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
    }
  ];
  public collectionVmsStatic: any[] = [
    {
      title: '№',
      property: 'index'
    },
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
    }
  ];

  public collectionUsers: any[] = [
    {
      title: '№',
      property: 'index'
    },
    {
      title: 'Имя пользователя',
      property: 'username',
      class: 'name-start',
      icon: 'user',
      type: 'string'
    }
  ];
  private idPool: number;
  public  typePool: string;
  public  menuActive: string = 'info';

  constructor(private activatedRoute: ActivatedRoute,
              private router: Router,
              private poolService: PoolDetailsService,
              public  dialog: MatDialog) {}

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.typePool = param.get('type');
      this.idPool = +param.get('id');
      this.getPool();
    });
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

  public clickVm(vm) {
    const vmActive = vm;
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
  private changeName() {
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
          name: this.pool.name,
          header: 'Редактирование имени пула',
          buttonAction: 'Редактировать'
        },
        update: {
          method: 'getPool',
          params: {
            id: this.idPool,
            type: this.typePool
          },
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
  }

  public close(): void  {
    this.router.navigate(['pools']);
  }
}
