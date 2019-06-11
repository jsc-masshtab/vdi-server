import { Component, OnInit, OnDestroy } from '@angular/core';
import { PoolsService } from '../pools.service';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { Subscription } from 'rxjs';

@Component({
  selector: 'vdi-pool-details',
  templateUrl: './pool-details.component.html',
  styleUrls: ['./pool-details.component.scss']
})


export class PoolDetailsComponent implements OnInit, OnDestroy {

  public pool: {} = {};
  private poolSub: Subscription;
  private name_pool: string = "";
  public collection = [
    {
      title: 'Название',
      property: 'name'
    },
    {
      title: 'Начальный размер пула',    // всего вм
      property: 'settings',
      property_lv2: 'initial_size'
    },
    {
      title: 'Размер пула',      // сколько свободных осталось
      property: 'settings',
      property_lv2: 'reserve_size'
    }
  ];

  public collection_vms = [
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
  public crumbs: object[] = [
    {
      title: 'Пулы виртуальных машин',
      icon: 'desktop'  
    }
  ];

  public spinner:boolean = false;

  constructor(private activatedRoute: ActivatedRoute,
              private service: PoolsService){}

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.pool_id = +param.get('id');
      this.getPool(this.pool_id);
    });
  }

  private getPool(id:number) {
    this.spinner = true;
    this.poolSub = this.service.getPool(id)
      .subscribe( (data) => {
        this.pool = data;
        this.addCrumb(this.pool['name']);
      
        this.spinner = false;
      },
      (error)=> {
        this.spinner = false;
      });
  }

  private addCrumb(poolName:string): boolean {

    if(this.name_pool === poolName) {
      return;
    }

    this.name_pool = poolName;
    this.crumbs[0]['route'] = 'pools';
        
    this.crumbs.push({
      title: `Пул ${ poolName }`,
      icon: 'desktop'
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

  ngOnDestroy() {
    this.poolSub.unsubscribe();
  }


}
