import { Component, OnInit } from '@angular/core';
import { PoolsService } from '../pools.service';
import { ActivatedRoute, ParamMap, Router } from '@angular/router';
import { MatDialog } from '@angular/material';
import { RemovePoolComponent } from '../remove-pool/remove-pool.component';


@Component({
  selector: 'vdi-pool-details',
  templateUrl: './pool-details.component.html'
})


export class PoolDetailsComponent implements OnInit {

  public host: boolean = false;

  public pool: {} = {};
  public collection = [
    {
      title: 'Название',
      property: 'name'
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
    }
  ];
  // Максимальное количество ВМ в пуле -  c тонкого клиента вм будут создаваться с каждым подключ. пользователем даже,если рес-сы закончатся

  public collection_vms = [
    {
      title: '№',
      property: 'index'
    },
    {
      title: 'Название',
      property: 'name'
    },
    {
      title: 'Сервер',
      property: "node",
      property_lv2: 'verbose_name'
    },
    {
      title: 'Шаблон',
      property: "template",
      property_lv2: 'name'
    }
  ];
  private pool_id:number;
  public menuActive:string = 'info';
  public into_spinner:boolean = false;

  constructor(private activatedRoute: ActivatedRoute,
              private router: Router,
              private service: PoolsService,
              public dialog: MatDialog){}

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.pool_id = +param.get('id');
      this.getPool();
    });
  }

  private getPool() {
    this.host = false;
    this.into_spinner = true;
    this.service.getPool(this.pool_id)
      .subscribe( (data) => {
        this.pool = data;

        this.into_spinner = false;
        this.host = true;
      },
      (error)=> {
        this.into_spinner = false;
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
