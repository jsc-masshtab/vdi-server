import { IParams } from '../../../../../../types';

import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Component, OnInit, ViewChild, ElementRef, OnDestroy, Input } from '@angular/core';
import { DatapoolsService } from './datapools.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';
import { DetailsMove } from 'src/app/dashboard/common/classes/details-move';
import { Subscription } from 'rxjs';


@Component({
  selector: 'vdi-datapools',
  templateUrl: './datapools.component.html',
  styleUrls: ['./datapools.component.scss']
})


export class DatapoolsComponent extends DetailsMove implements OnInit, OnDestroy {

  @Input() filter: object

  public datapools: object[] = [];
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'folder-open',
      sort: true
    },
    {
      title: 'Тип',
      property: 'type',
      type: 'string',
      sort: true
    },
    {
      title: 'Свободно (МБ)',
      property: 'free_space',
      type: 'string',
      sort: true
    },
    {
      title: 'Занято (МБ)',
      property: 'used_space',
      type: 'string',
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
      title: 'Статус',
      property: 'status',
      sort: true
    }
  ];

  private sub: Subscription;


  constructor(private service: DatapoolsService, private waitService: WaitService,  private router: Router) {
    super();
  }

  @ViewChild('view') view: ElementRef;

  ngOnInit() {
    this.getDatapools();
  }

  public getDatapools() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
    this.waitService.setWait(true);

    let filtered = (data) => {
      if (this.filter) {
        return data.data.controller.data_pools
      } else {
        return data.data.datapools
      }
    }

    this.sub = this.service.getAllDatapools(this.filter).valueChanges.pipe(map(data => filtered(data)))
      .subscribe( (data) => {
        this.datapools = data;
        this.waitService.setWait(false);
      });
  }

  public routeTo(datapool): void {

    let datapool_id = datapool.id
    let controller_id = ''

    if (this.filter) {
      controller_id = this.filter['controller_id']
    } else {
      controller_id = datapool.controller.id;
    }

    this.router.navigate([`pages/resourses/datapools/${controller_id}/${datapool_id}`]);
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

  public sortList(param: IParams): void  {
    this.service.paramsForGetDatapools.spin = param.spin;
    this.service.paramsForGetDatapools.nameSort = param.nameSort;
    this.getDatapools();
  }

  ngOnDestroy() {
    this.service.paramsForGetDatapools.spin = true;
    this.service.paramsForGetDatapools.nameSort = undefined;
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }

}
