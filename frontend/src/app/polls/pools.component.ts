import { Component, OnInit } from '@angular/core';
import { PoolsService } from './pools.service';
import { PoolAddComponent } from './pool-add/pool-add.component';
import { Router } from '@angular/router';

import { MatDialog } from '@angular/material';
import { Subscription } from 'rxjs';
import { RemovePoolComponent } from './remove-pool/remove-pool.component';

@Component({
  selector: 'vdi-pools',
  templateUrl: './pools.component.html',
  styleUrls: ['./pools.component.scss']
})

export class PoolsComponent implements OnInit {

  public pools: [];
  public spinner:boolean = true;
  private getPoolsSub: Subscription;

  public collection: object[] = [
    {
      title: '№',
      property: 'index'
    },
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
    },
    {
      title: 'Доступные ВМ',
      property: 'state',
      property_lv2_array: 'available'
    }
  ];

  public crumbs: object[] = [
    {
      title: 'Пулы виртуальных машин',
      icon: 'desktop'
    }
  ];

  constructor(private service: PoolsService,public dialog: MatDialog,private router: Router){}

  ngOnInit() {
    this.getAllPools();
  }

  public openCreatePool() {
    this.dialog.open(PoolAddComponent, {
      width: '500px'
    });
  }

  public removePool() {
    this.dialog.open(RemovePoolComponent, {
      width: '500px'
    });
  }

  private getAllPools() {
    this.getPoolsSub = this.service.getAllPools(true)
      .subscribe( (data) => {
        this.pools = data;
        this.spinner = false;
      },
      (error) => {
        this.spinner = false;
      });
  }

  public routeTo(event): void {
    this.router.navigate([`pools/${event.id}`]);
  }

  ngOnDestroy() {
    this.getPoolsSub.unsubscribe();
  }

}
