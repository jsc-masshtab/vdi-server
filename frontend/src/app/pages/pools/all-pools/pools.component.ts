import { Component, OnInit, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';

import { WaitService } from '@core/components/wait/wait.service';

import { DetailsMove } from '@shared/classes/details-move';
import { WebsocketService } from '@shared/classes/websock.service';
import { IParams } from '@shared/types';

import { PoolAddComponent } from '../add-pool/add-pool.component';
import { PoolsService } from './pools.service';



@Component({
  selector: 'vdi-pools',
  templateUrl: './pools.component.html',
  styleUrls: ['./pools.component.scss']
})

export class PoolsComponent extends DetailsMove implements OnInit, OnDestroy {

  private getPoolsSub: Subscription;
  private getControllerssSub: Subscription;
  private socketSub: Subscription;

  public pools: [];
  public controllers: any[] = [];

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
      property_lv2: 'verbose_name',
      sort: true
    },
    {
      title: 'Количество доступных ВМ',
      property: 'vm_amount',
      type: 'string',
      sort: true
    },
    {
      title: 'Пользователи',
      property: 'users',
      type: 'array-length',
      sort: true
    },
    {
      title: 'Тип',
      property: 'pool_type',
      type: 'pool_type',
      sort: true
    },
    {
      title: 'Cтатус',
      property: 'status',
      sort: true
    }
  ];


  constructor(
    private service: PoolsService,
    public dialog: MatDialog,
    private router: Router,
    private waitService: WaitService,
    private ws: WebsocketService
  ) {
    super();
  }

  @ViewChild('view', { static: true }) view: ElementRef;

  ngOnInit() {
    this.checkControllers()
    this.getAllPools();
    this.listenSockets();
  }

  public openCreatePool(): void {
    this.dialog.open(PoolAddComponent, {
      disableClose: true,
      width: '500px'
    });
  }

  public checkControllers() {

    if (this.getControllerssSub) {
      this.getControllerssSub.unsubscribe();
    }

    this.getControllerssSub = this.service.getAllControllers().valueChanges.pipe(map(data => data.data['controllers']))
      .subscribe((data) => {
        this.controllers = data;
      });
  }

  public getAllPools(): void {
    if (this.getPoolsSub) {
      this.getPoolsSub.unsubscribe();
    }

    this.waitService.setWait(true);

    this.getPoolsSub = this.service.getAllPools().valueChanges.pipe(map(data => data.data['pools']))
      .subscribe((data) => {
        this.pools = data;
        this.waitService.setWait(false);
      });
  }

  private listenSockets() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }

    this.socketSub = this.ws.stream('/pools/').subscribe((message: any) => {
      if (message['msg_type'] === 'data') {
        this.service.getAllPools().refetch();
      }
    });
  }

  public refresh(): void {
    this.service.paramsForGetPools.spin = true;
    this.getAllPools();
  }

  public routeTo(event): void {
    const desktopPoolType: string = event.pool_type.toLowerCase();
    this.router.navigate([`pages/pools/${desktopPoolType}/${event.pool_id}`]);
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
    let output_param = param.nameSort;
    this.service.paramsForGetPools.spin = param.spin;
    switch (output_param) {
      case 'vms':
        output_param = 'vms_count';
        break;
      case '-vms':
        output_param = '-vms_count';
        break;
      case 'users':
        output_param = 'users_count';
        break;
      case '-users':
        output_param = '-users_count';
        break;
      default:
        output_param = param.nameSort;
    }
    this.service.paramsForGetPools.nameSort = output_param;
    this.getAllPools();
  }

  ngOnDestroy() {
    this.getPoolsSub.unsubscribe();
    this.service.paramsForGetPools.spin = true;
    this.service.paramsForGetPools.nameSort = undefined;

    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }
  }
}
