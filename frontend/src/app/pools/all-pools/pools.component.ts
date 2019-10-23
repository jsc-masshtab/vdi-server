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
      property: 'name',
      class: 'name-start',
      icon: 'desktop',
      type: 'string',
      sort: false
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'ip',
      sort: false
    },
    {
      title: 'Доступные ВМ',
      property: 'vms',
      type: 'array-length',
      sort: false
    },
    {
      title: 'Пользователи',
      property: 'users',
      type: {
        propertyDepend: 'username',
        typeDepend: 'propertyInObjectsInArray'
      },
      sort: false
    },
    {
      title: 'Тип',
      property: 'desktop_pool_type',
      type: 'string',
      sort: false
    },
    {
      title: 'Cтатус',
      property: 'status',
      sort: false
    }
  ];


  constructor(private service: PoolsService, public dialog: MatDialog, private router: Router, private waitService: WaitService) {
    super();
  }

  @ViewChild('view') view: ElementRef;

  ngOnInit() {
    this.getAllPools({ spin: true });
  }

  public openCreatePool(): void {
    this.dialog.open(PoolAddComponent, {
      width: '500px'
    });
  }

  public getAllPools(param: IParams): void {
    if (param && param.spin) {
      this.waitService.setWait(true);
    }

    if (this.getPoolsSub) {
      this.getPoolsSub.unsubscribe();
    }

    console.log(param,'param');
    this.getPoolsSub = this.service.getAllPools(param)
      .subscribe((data) => {
        this.pools = data;
        console.log('прилетели пулы',this.pools);
        if (param && param.spin) {
          this.waitService.setWait(false);
        }
      });
  }

  public routeTo(event): void {
    const desktopPoolType: string = event.desktop_pool_type.toLowerCase();
    this.router.navigate([`pools/${desktopPoolType}/${event.id}`]);
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

  public sortList(param: {nameSort: string, reverse: boolean, spin: boolean }) {
    console.log(param);
    this.paramsForGetPools['spin'] = param.spin; // чтобы сохранить при refresh сортировку
    this.paramsForGetPools['nameSort'] = param.nameSort;
    this.paramsForGetPools['reverse'] = param.reverse;
    this.getAllPools(this.paramsForGetPools);
  }

  ngOnDestroy() {
    this.getPoolsSub.unsubscribe();
  }

}
