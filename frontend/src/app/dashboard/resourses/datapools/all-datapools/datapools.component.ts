import { IParams } from '../../../../../../types';

import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Component, OnInit, ViewChild, ElementRef, OnDestroy } from '@angular/core';
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
      title: 'Диски',
      property: 'vdisk_count',
      type: 'string',
      sort: true
    },
    {
      title: 'Образы',
      property: 'iso_count',
      type: 'string',
      sort: true
    },
    {
      title: 'Файлы',
      property: 'file_count',
      type: 'string',
      sort: true
    },
    {
      title: 'Свободно (Мб)',
      property: 'free_space',
      type: 'string',
      sort: true
    },
    {
      title: 'Занято (Мб)',
      property: 'used_space',
      type: 'string',
      sort: true
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'address',
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
    this.sub = this.service.getAllDatapools().valueChanges.pipe(map(data => data.data.datapools))
      .subscribe( (data) => {
        this.datapools = data;
        this.waitService.setWait(false);
      });
  }

  public routeTo(event): void {
    this.router.navigate([`pages/resourses/datapools/${event.controller.address}/${event.id}`]);
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
