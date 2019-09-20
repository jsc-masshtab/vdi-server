import { VmDetalsPopupComponent } from './vm-details-popup/vm-details-popup.component';
import { RemoveUsersPoolComponent } from './../remove-users/remove-users.component';
import { AddUsersPoolComponent } from './../add-users/add-users.component';
import { RemoveVMStaticPoolComponent } from './../remove-vms/remove-vms.component';
import { AddVMStaticPoolComponent } from './../add-vms/add-vms.component';
import { Component, OnInit } from '@angular/core';
import { PoolsService } from '../pools.service';
import { ActivatedRoute, ParamMap, Router } from '@angular/router';
import { MatDialog } from '@angular/material';
import { RemovePoolComponent } from '../remove-pool/remove-pool.component';

interface type_pool {
  [key: string] : any
}

@Component({
  selector: 'vdi-pool-details',
  templateUrl: './pool-details.component.html'
})


export class PoolDetailsComponent implements OnInit {

  public host: boolean = false;

  public pool: type_pool = {};
  public collection_details_static:any[] = [
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
  public collection_details_automated:any[] = [
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
      title: 'Максимальное количество создаваемых ВМ',  // Максимальное количество ВМ в пуле -  c тонкого клиента вм будут создаваться с каждым подключ. пользователем даже,если рес-сы закончатся
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

  public collection_vms_automated:any[] = [
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
      property: "template",
      property_lv2: 'name'
    },
    {
      title: 'Пользователь',
      property: "user",
      property_lv2: 'username'
    },
    {
      title: 'Состояние',
      property: "state"
    }
  ];
  public collection_vms_static:any[] = [
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
      property: "user",
      property_lv2: 'username'
    },
    {
      title: 'Состояние',
      property: "state"
    }
  ];

  public collection_users:any[] = [
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
  private pool_id:number;
  private pool_type:string;
  public  menuActive:string = 'info';

  constructor(private activatedRoute: ActivatedRoute,
              private router: Router,
              private service: PoolsService,
              public dialog: MatDialog) {}

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.pool_type = param.get('type');
      this.pool_id = +param.get('id');
      this.getPool();
    });
  }

  public getPool() {
    this.host = false;
    this.service.getPool(this.pool_id,this.pool_type)
      .subscribe( (data) => {
        this.pool = data;
        this.host = true;
      },
      ()=> {
        this.host = true;
      });
  }

  public removePool() {
    this.dialog.open(RemovePoolComponent, {
      width: '500px',
      data: {
        pool_id: this.pool_id,
        pool_name: this.pool['name']
      }
    });
  }

  public addUsers() {
    this.dialog.open(AddUsersPoolComponent, {
      width: '500px',
      data: {
        pool_id: this.pool_id,
        pool_name: this.pool['name'],
        pool_type: this.pool_type
      }
    });
  }

  public removeUsers() {
    this.dialog.open(RemoveUsersPoolComponent, {
      width: '500px',
      data: {
        pool_id: this.pool_id,
        pool_name: this.pool['name'],
        pool_type: this.pool_type
      }
    });
  }

  public addVM() {
    this.dialog.open(AddVMStaticPoolComponent, {
      width: '500px',
      data: {
        pool_id: this.pool_id,
        pool_name: this.pool['name'],
        id_cluster: this.pool['settings']['cluster_id'],
        id_node: this.pool['settings']['node_id'],
        pool_type: this.pool_type
      }
    });
  }

  public removeVM() {
    this.dialog.open(RemoveVMStaticPoolComponent, {
      width: '500px',
      data: {
        pool_id: this.pool_id,
        pool_name: this.pool['name'],
        vms: this.pool.vms,
        pool_type: this.pool_type
      }
    });
  }

  public clickVm(vm) {
    this.dialog.open(VmDetalsPopupComponent, {
      width: '50%',
      data: {
        vm: vm,
        pool_type: this.pool_type,
        pool_users: this.pool.users,
        pool_id: this.pool_id
      }
    });
  }

  public routeTo(route: string): void {
    if(route === 'info') {
      this.menuActive = 'info';
    }

    if(route === 'vms') {
      this.menuActive = 'vms';
    }

    if(route === 'users') {
      this.menuActive = 'users';
    }
  }

  public close() {
    this.router.navigate(['pools']);
  }
}
