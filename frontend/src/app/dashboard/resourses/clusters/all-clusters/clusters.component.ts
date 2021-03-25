import { IParams } from '../../../../../../types';
import { DetailsMove } from '../../../common/classes/details-move';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Component, OnInit, ViewChild, ElementRef, OnDestroy, Input } from '@angular/core';
import { ClustersService } from './clusters.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { WebsocketService } from 'src/app/dashboard/common/classes/websock.service';

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
      title: 'RAM',
      property: 'memory_count',
      type: 'bites',
      delimiter: 'Мб',
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
  private socketSub: Subscription;

  constructor(
    private service: ClustersService,
    private router: Router,
    private waitService: WaitService,
    private ws: WebsocketService
  ) {
    super();
  }

  @ViewChild('view', { static: true }) view: ElementRef;

  ngOnInit() {
    this.getAllClusters();
    this.listenSockets();
  }

  private listenSockets() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }

    this.socketSub = this.ws.stream('/clusters/').subscribe((message: any) => {
      if (message['msg_type'] === 'data') {
        this.service.getAllClusters(this.filter).refetch();
      }
    });
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

  public routeTo(cluster): void {

    let cluster_id = cluster.id
    let controller_id = ''

    if (this.filter) {
      controller_id = this.filter['controller_id']
    } else {
      controller_id = cluster.controller.id;
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

    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }
  }

}
