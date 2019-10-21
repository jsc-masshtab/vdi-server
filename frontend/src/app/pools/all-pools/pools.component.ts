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
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'ip'
    },
    {
      title: 'Доступные ВМ',
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
    },
    {
      title: 'Тип',
      property: 'desktop_pool_type',
      type: 'string'
    },
    {
      title: 'Cтатус',
      property: 'status'
    }
  ];

  constructor(private service: PoolsService, public dialog: MatDialog, private router: Router, private waitService: WaitService) {
    super();
  }

  @ViewChild('view') view: ElementRef;

  ngOnInit() {
    this.getAllPools({ spin: true, obs: true });
  }

  public openCreatePool(): void {
    this.dialog.open(PoolAddComponent, {
      width: '500px'
    });
  }

  public getAllPools(param?: { readonly spin?: boolean,  readonly obs?: boolean }): void {
    if (param && param.spin) {
      this.waitService.setWait(true);
    }
    this.getPoolsSub = this.service.getAllPools(param.obs)
      .subscribe((data) => {
        this.pools = data;
        if (param && param.spin) {
          this.waitService.setWait(false);
          param = {};
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

  ngOnDestroy() {
    this.getPoolsSub.unsubscribe();
  }

}
