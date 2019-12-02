import { IParams } from './../../../../types/index.d';
import { PoolAddComponent } from './../add-pool/add-pool.component';
import { WaitService } from './../../common/components/single/wait/wait.service';

import { Component, OnInit, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { PoolsService } from './pools.service';

import { Router } from '@angular/router';
import { MatDialog } from '@angular/material';
import { Subscription } from 'rxjs';
import { DetailsMove } from 'src/app/common/classes/details-move';


@Component({
  selector: 'vdi-pools',
  templateUrl: './pools.component.html',
  styleUrls: ['./pools.component.scss']
})

export class PoolsComponent extends DetailsMove implements OnInit, OnDestroy {

  public pools: [];
  private getPoolsSub: Subscription;

  public collection: ReadonlyArray<object> = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'desktop',
      type: 'string',
      sort: true
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'address',
      sort: true
    },
    {
      title: 'Доступные ВМ',
      property: 'vms',
      type: 'array-length',
      sort: true
    },
    {
      title: 'Пользователи',
      property: 'users',
      type: {
        propertyDepend: 'username',
        typeDepend: 'propertyInObjectsInArray'
      },
      sort: true
    },
    {
      title: 'Тип',
      property: 'pool_type',
      type: 'string',
      sort: true
    },
    {
      title: 'Cтатус',
      property: 'status',
      sort: true
    }
  ];


  constructor(private service: PoolsService, public dialog: MatDialog,
              private router: Router, private waitService: WaitService) {
    super();
  }

  @ViewChild('view') view: ElementRef;

  ngOnInit() {
    this.getAllPools();
  }

  public openCreatePool(): void {
    this.dialog.open(PoolAddComponent, {
      width: '500px'
    });
  }

  public getAllPools(): void {
    if (this.getPoolsSub) {
      this.getPoolsSub.unsubscribe();
    }

    this.getPoolsSub = this.service.getAllPools()
      .subscribe((data) => {
        this.pools = data;
        if (this.service.paramsForGetPools.spin) {
          this.waitService.setWait(false);
        }
      });
  }

  public refresh(): void {
    this.service.paramsForGetPools['spin'] = true;
    this.getAllPools();
  }

  public routeTo(event): void {
    console.log(event);
    const desktopPoolType: string = event.pool_type.toLowerCase();
    this.router.navigate([`pools/${desktopPoolType}/${event.pool_id}`]);
  }

  public onResize(): void {
    super.onResize(this.view);
  }

  public componentActivate(): void {
    super.componentActivate(this.view);
  }

  public componentDeactivate(): void {
    super.componentDeactivate();
  }

  public sortList(param: IParams) {
    console.log(param, 'in pool');
    this.service.paramsForGetPools.spin = param.spin;
    this.service.paramsForGetPools.nameSort = param.nameSort;
    this.service.paramsForGetPools.reverse = param.reverse;
    this.getAllPools();
  }

  ngOnDestroy() {
    this.getPoolsSub.unsubscribe();
    this.service.paramsForGetPools.spin = true;
    this.service.paramsForGetPools.nameSort = undefined;
    this.service.paramsForGetPools.reverse = undefined;
  }

}
