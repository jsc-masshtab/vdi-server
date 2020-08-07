import { PoolsUpdateService } from './pools.update.service';
import { IParams } from '../../../../../types';
import { PoolAddComponent } from '../add-pool/add-pool.component';
import { WaitService } from '../../common/components/single/wait/wait.service';

import { Component, OnInit, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { PoolsService } from './pools.service';

import { Router } from '@angular/router';
import { MatDialog } from '@angular/material';
import { Subscription } from 'rxjs';
import { DetailsMove } from 'src/app/dashboard/common/classes/details-move';


@Component({
  selector: 'vdi-pools',
  templateUrl: './pools.component.html',
  styleUrls: ['./pools.component.scss']
})

export class PoolsComponent extends DetailsMove implements OnInit, OnDestroy {

  public pools: [];
  private getPoolsSub: Subscription;
  private updateSub: Subscription;

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
              private router: Router, private waitService: WaitService,
              private update: PoolsUpdateService) {
    super();
  }

  @ViewChild('view') view: ElementRef;

  ngOnInit() {
    this.getAllPools({wait: true});
    this.updatePools();
  }

  private updatePools(): void {
    this.updateSub = this.update.getUpdate().subscribe((param: string) => {
      if (param === 'update') {
        this.service.paramsForGetPools.spin = false;
        this.getAllPools({wait: false});
      }
    });
  }

  public openCreatePool(): void {
    this.dialog.open(PoolAddComponent, {
 			disableClose: true, 
      width: '500px'
    });
  }

  public getAllPools(wait: { wait: boolean}): void {
    if (this.getPoolsSub) {
      this.getPoolsSub.unsubscribe();
    }
    this.getPoolsSub = this.service.getAllPools()
      .subscribe((data) => {
        this.pools = data;
        if (wait.wait) {
          this.waitService.setWait(false);
          wait.wait = false; // чтобы не отправлял в waitService при obs$ = timer(0, 60000);
        }
    });
  }

  public refresh(): void {
    this.service.paramsForGetPools.spin = true;
    this.getAllPools({wait: true});
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
    this.getAllPools({wait: true});
  }

  ngOnDestroy() {
    this.getPoolsSub.unsubscribe();
    this.updateSub.unsubscribe();
    this.service.paramsForGetPools.spin = true;
    this.service.paramsForGetPools.nameSort = undefined;
  }

}
