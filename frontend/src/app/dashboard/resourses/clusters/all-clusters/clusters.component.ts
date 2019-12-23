import { IParams } from '../../../../../../types';
import { DetailsMove } from '../../../common/classes/details-move';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Component, OnInit, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { ClustersService } from './clusters.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';

@Component({
  selector: 'vdi-clusters',
  templateUrl: './clusters.component.html',
  styleUrls: ['./clusters.component.scss']
})


export class ClustersComponent extends DetailsMove implements OnInit, OnDestroy {

  public clusters = [];
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'building',
      sort: true
    },
    {
      title: 'Серверы',
      property: 'nodes_count',
      type: 'string',
      sort: true
    },
    {
      title: 'CPU',
      property: 'cpu_count',
      type: 'string',
      sort: true
    },
    {
      title: 'RAM',
      property: 'memory_count',
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
      title: 'Статус',
      property: 'status',
      sort: true
    }
  ];


  constructor(private service: ClustersService, private router: Router, private waitService: WaitService) {
    super();
  }

  @ViewChild('view') view: ElementRef;

  ngOnInit() {
    this.getAllClusters();
  }

  public getAllClusters(): void {
    this.waitService.setWait(true);
    this.service.getAllClusters().valueChanges.pipe(map(data => data.data.clusters))
      .subscribe((data) => {
        console.log('all cl');
        this.clusters = data;
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

  public routeTo(event): void {
    this.router.navigate([`pages/resourses/clusters/${event.controller.address}/${event.id}`]);
  }

  public sortList(param: IParams) {
    this.service.paramsForGetClusters.spin = param.spin;
    this.service.paramsForGetClusters.nameSort = param.nameSort;
    this.getAllClusters();
  }

  ngOnDestroy() {
    this.service.paramsForGetClusters.spin = true;
    this.service.paramsForGetClusters.nameSort = undefined;
  }

}
