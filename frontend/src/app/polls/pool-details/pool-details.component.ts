import { Component, OnInit } from '@angular/core';
import { PoolsService } from '../pools.service';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap } from '@angular/router';

@Component({
  selector: 'vdi-pool-details',
  templateUrl: './pool-details.component.html',
  styleUrls: ['./pool-details.component.scss']
})


export class PoolDetailsComponent implements OnInit {

  public pool: {} = {};
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
      property: "node"
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
    this.service.getPool(id).valueChanges.pipe(map(data => data.data.pool))
      .subscribe( (data) => {
        this.pool = data;
        console.log(this.pool);
        this.crumbs[0]['route'] = 'pools';
        
        this.crumbs.push({
          title: `Пул ${ this.pool['name'] }`,
          icon: 'desktop'
        });
      
        this.spinner = false;
      },
      (error)=> {
        this.spinner = false;
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


}
