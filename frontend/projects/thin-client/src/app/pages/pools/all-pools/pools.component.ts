import { Component, OnInit, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';


import { DetailsMove } from '@shared/classes/details-move';
import { IParams } from '@shared/types';
import { WaitService } from '../../../core/wait/wait.service';
import {  PoolsService } from '../pools.service';
import { IPoolClient, PoolMapper } from './pools.mapper';



@Component({
  selector: 'app-pools',
  templateUrl: './pools.component.html',
  styleUrls: ['./pools.component.scss']
})

export class PoolsComponent extends DetailsMove implements OnInit, OnDestroy {

  private getPoolsSub: Subscription;
  public pools: IPoolClient[];
  public controllers: any[] = [];
  
  public collection: ReadonlyArray<object> = [
    {
      title: 'Название',
      property: 'name',
      class: 'name-start',
      icon: 'desktop',
      type: 'string',
      sort: true
    },
    {
      title: 'Cтатус',
      property: 'status',
      sort: true
    }
  ];


  constructor(
    private poolService: PoolsService,
    private router: Router,
    private waitService: WaitService,
  ) {
    super();
  }

  @ViewChild('view', { static: true }) view: ElementRef;

  ngOnInit() {
    this.getAllPools();
  }

  public getAllPools(): void {
 

    this.waitService.setWait(true);

    this.getPoolsSub = this.poolService.getPools().subscribe((res) => {
        this.pools =  res.data.map( pool => PoolMapper.transformToClient(pool));
        
        this.waitService.setWait(false);
      });
  }



  public refresh(): void {
    this.poolService.paramsForGetPools.spin = true;
    this.getAllPools();
  }

  public routeTo(event: IPoolClient): void {    
    const {connectionTypes} = event;
    
    this.router.navigate([`pages/pools/${event.id}`], {state: {data: connectionTypes}});
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
    this.poolService.paramsForGetPools.spin = param.spin;
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
    this.poolService.paramsForGetPools.nameSort = output_param;
    this.getAllPools();
  }

  public ngOnDestroy() {
    this.getPoolsSub.unsubscribe();
    this.poolService.paramsForGetPools.spin = true;
    this.poolService.paramsForGetPools.nameSort = undefined;
  }


}
