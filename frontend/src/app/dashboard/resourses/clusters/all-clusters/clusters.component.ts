import { IParams } from '../../../../../../types';
import { DetailsMove } from '../../../common/classes/details-move';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Component, OnInit, ViewChild, ElementRef, OnDestroy, Input } from '@angular/core';
import { ClustersService } from './clusters.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

@Component({
  selector: 'vdi-clusters',
  templateUrl: './clusters.component.html',
  styleUrls: ['./clusters.component.scss']
})


export class ClustersComponent extends DetailsMove implements OnInit, OnDestroy {

  @Input() filter: object

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
      title: 'RAM (MB)',
      property: 'memory_count',
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
      title: 'Статус',
      property: 'status',
      sort: true
    }
  ];

  private sub: Subscription;


  constructor(private service: ClustersService, private router: Router, private waitService: WaitService) {
    super();
  }

  @ViewChild('view') view: ElementRef;

  ngOnInit() {
    this.getAllClusters();
  }

  public getAllClusters(): void {
    if (this.sub) {
      this.sub.unsubscribe();
    }
    this.waitService.setWait(true);

    let filtered = (data) => {
      if (this.filter) {
        return data.data.controller.clusters
      } else {
        return data.data.clusters
      }
    }

    this.sub = this.service.getAllClusters(this.filter).valueChanges.pipe(map(data => filtered(data)))
      .subscribe((data) => {
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

    let cluster_id = event.id
    let controller_id = ''

    if (this.filter) {
      controller_id = this.filter['controller_id']
    } else {
      controller_id = event.controller.id;
    }

    this.router.navigate([`pages/resourses/clusters/${controller_id}/${cluster_id}`]);
  }

  public sortList(param: IParams) {
    this.service.paramsForGetClusters.spin = param.spin;
    this.service.paramsForGetClusters.nameSort = param.nameSort;
    this.getAllClusters();
  }

  ngOnDestroy() {
    this.service.paramsForGetClusters.spin = true;
    this.service.paramsForGetClusters.nameSort = undefined;
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }

}
