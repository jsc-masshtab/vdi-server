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
      property: 'name'
    },
    {
      title: 'Тип',
      property: 'desktop_pool_type'
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
      property_array: 'vms'
    },
    {
      title: 'Пользователи',
      property_array_prop: 'users',
      property_array_prop_lv2: 'username'
    }
  ];
  public collectionDetailsAutomated: any[] = [
    {
      title: 'Название',
      property: 'name'
    },
    {
      title: 'Тип',
      property: 'desktop_pool_type'
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
      property_array: 'vms'
    },
    {
      title: 'Пользователи',
      property_array_prop: 'users',
      property_array_prop_lv2: 'username'
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
      icon: 'desktop'
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
      title: 'Состояние',
      property: 'state'
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
      icon: 'desktop'
    },
    {
      title: 'Пользователь',
      property: 'user',
      property_lv2: 'username'
    },
    {
      title: 'Состояние',
      property: 'state'
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
      icon: 'user'
    }
  ];
  private idPool: number;
  private typePool: string;
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

  public getPool() {
    this.host = false;
    this.poolService.getPool(this.idPool, this.typePool)
      .subscribe( (data) => {
        this.pool = data;
        this.host = true;
      },
      () => {
        this.host = true;
      });
  }

  public removePool() {
    const a = this.dialog.open(RemovePoolComponent, {
      width: '500px',
      data: {
        idPool: this.idPool,
        namePool: this.pool.name
      }
    });

    console.log(a);
  }

  public addUsers() {
    this.dialog.open(AddUsersPoolComponent, {
      width: '500px',
      data: {
        pool_id: this.idPool,
        pool_name: this.pool.name,
        typePool: this.typePool
      }
    });
  }

  public removeUsers() {
    this.dialog.open(RemoveUsersPoolComponent, {
      width: '500px',
      data: {
        pool_id: this.idPool,
        pool_name: this.pool.name,
        typePool: this.typePool
      }
    });
  }

  public addVM() {
    this.dialog.open(AddVMStaticPoolComponent, {
      width: '500px',
      data: {
        pool_id: this.idPool,
        pool_name: this.pool.name,
        id_cluster: this.pool.settings.cluster_id,
        id_node: this.pool.settings.node_id,
        typePool: this.typePool
      }
    });
  }

  public removeVM() {
    this.dialog.open(RemoveVMStaticPoolComponent, {
      width: '500px',
      data: {
        pool_id: this.idPool,
        pool_name: this.pool.name,
        vms: this.pool.vms,
        typePool: this.typePool
      }
    });
  }

  // public clickVm(vm) {
  //   const vmActive = vm;
  //   this.dialog.open(VmDetalsPopupComponent, {
  //     width: '50%',
  //     data: {
  //       vm: vmActive,
  //       typePool: this.typePool,
  //       pool_users: this.pool.users,
  //       pool_id: this.idPool
  //     }
  //   });
  // }

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
