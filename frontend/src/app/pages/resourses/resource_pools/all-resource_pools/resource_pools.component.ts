import { Component, OnInit, ViewChild, ElementRef, OnDestroy, Input } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';

import { IParams } from '../../../../shared/types';
import { WaitService } from '../../../../core/components/wait/wait.service';
import { DetailsMove } from '../../../../shared/classes/details-move';
import { ResourcePoolsService } from './resource_pools.service';


@Component({
  selector: 'vdi-resource_pools',
  templateUrl: './resource_pools.component.html',
  styleUrls: ['./resource_pools.component.scss']
})


export class ResourcePoolsComponent extends DetailsMove implements OnInit, OnDestroy {

  @Input() filter: object

  public resource_pools = [];
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'database',
      sort: true
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'verbose_name',
      type: 'string',
      sort: true
    },
    {
      title: 'Количество ВМ',
      property: 'domains_count',
      type: 'string',
      sort: true
    },
    {
      title: 'Ограничение памяти',
      property: 'memory_limit',
      type: 'bites',
      delimiter: 'Мб',
      sort: true
    },
    {
      title: 'Ограничение vcpu',
      property: 'cpu_limit',
      type: 'string',
      sort: true
    }
  ];

  private sub: Subscription;


  constructor(private service: ResourcePoolsService, private router: Router, private waitService: WaitService) {
    super();
  }

  @ViewChild('view', { static: true }) view: ElementRef;

  ngOnInit() {
    this.getResourcePools();
  }

  public getResourcePools(): void {
    if (this.sub) {
      this.sub.unsubscribe();
    }
    this.waitService.setWait(true);

    let filtered = (data) => {
      if (this.filter) {
        return data.data.controller.resource_pools
      } else {
        return data.data.resource_pools
      }
    }

    this.sub = this.service.getAllResourcePools(this.filter).valueChanges.pipe(map(data => filtered(data)))
      .subscribe((data) => {
        this.resource_pools = data;
        this.waitService.setWait(false);
      });
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

  public routeTo(resource_pool): void {

    let resource_pools_id = resource_pool.id
    let controller_id = ''

    if (this.filter) {
      controller_id = this.filter['controller_id']
    } else {
      controller_id = resource_pool.controller.id;
    }

    this.router.navigate([`pages/resourses/resource_pools/${controller_id}/${resource_pools_id}`]);
  }

  public sortList(param: IParams) {
    this.service.paramsForGetResourcePools.spin = param.spin;
    this.service.paramsForGetResourcePools.nameSort = param.nameSort;
    this.getResourcePools();
  }

  ngOnDestroy() {
    this.service.paramsForGetResourcePools.spin = true;
    this.service.paramsForGetResourcePools.nameSort = undefined;
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }

}
