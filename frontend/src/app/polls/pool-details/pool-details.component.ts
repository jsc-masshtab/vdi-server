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
  public collection_static:any[] = [
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
      title: 'Всего ВМ',
      property_array: 'vms'
    }
  ];
  public collection_automated:any[] = [
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
    }
  ];
  
  public collection_vms_automated:any[] = [
    {
      title: '№',
      property: 'index'
    },
    {
      title: 'Название',
      property: 'name'
    },
    {
      title: 'Шаблон',
      property: "template",
      property_lv2: 'name'
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
      property: 'name'
    },
    {
      title: 'Состояние',
      property: "state"
    }
  ];
  private pool_id:number;
  private pool_type:string;
  public  menuActive:string = 'info';

  constructor(private activatedRoute: ActivatedRoute,
              private router: Router,
              private service: PoolsService,
              public dialog: MatDialog){}

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
      (error)=> {
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

  public addVM() {
    this.dialog.open(AddVMStaticPoolComponent, {
      width: '500px',
      data: {
        pool_id: this.pool_id,
        pool_name: this.pool['name'],
        id_cluster: this.pool['cluster_id'],
        id_node: this.pool['node_id'],
        id_datapool: this.pool['datapool_id']
      }
    });
  }

  public routeTo(route:string): void {
    if(route === 'info') {
      this.menuActive = 'info';
    }

    if(route === 'vms') {
      this.menuActive = 'vms';
    }
  }

  public close() {
    this.router.navigate(['pools']);
  }
}
