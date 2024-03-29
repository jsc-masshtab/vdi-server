import { Component, OnInit, ViewChild, ElementRef, OnDestroy, Input } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';

import { WaitService } from '@core/components/wait/wait.service';
import { WebsocketService } from '@app/core/services/websock.service';
import { DetailsMove } from '@shared/classes/details-move';
import { IParams } from '@shared/types';
import { NodesService } from './nodes.service';

@Component({
  selector: 'vdi-nodes',
  templateUrl: './nodes.component.html',
  styleUrls: ['./nodes.component.scss']
})
export class NodesComponent extends DetailsMove implements OnInit, OnDestroy {

  @Input() filter: object

  public limit = 100;
  public count = 0;
  public offset = 0;
  public queryset: any;

  public refresh: boolean = false

  public infoTemplates: [];
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'server',
      sort: true
    },
    {
      title: 'Локация',
      property: 'datacenter_name',
      type: 'string',
      sort: true
    },
    {
      title: 'IP адрес',
      property: 'management_ip',
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

  public nodes: object[] = [];

  private sub: Subscription;
  private socketSub: Subscription;

  constructor(
    private service: NodesService,
    private router: Router,
    private waitService: WaitService,
    private ws: WebsocketService
  ) {
    super();
  }

  @ViewChild('view', { static: true }) view: ElementRef;

  ngOnInit() {
    this.getNodes();
    this.listenSockets();
  }

  private listenSockets() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }

    this.socketSub = this.ws.stream('/nodes/').subscribe((message: any) => {
      if (message['msg_type'] === 'data') {
        this.service.getAllNodes(this.filter).refetch();
      }
    });
  }

  public toPage(message: any): void {
    this.offset = message.offset;
    this.getNodes();
  }

  public getNodes(refresh?) {
    if (this.sub) {
      this.sub.unsubscribe();
    }

    const queryset = {
      offset: this.offset,
      limit: this.limit
    }

    this.queryset = queryset;

    this.waitService.setWait(true);

    let filtered = (data) => {
      if ((this.filter && !this.refresh) || (this.filter && this.refresh)) {
        return data.data.controller
      } else {
        return data.data.nodes_with_count
      }
    }

    if (refresh) {
      this.refresh = refresh
    }

    this.sub = this.service.getAllNodes({
      ...this.filter,
      ...queryset
    }, this.refresh).valueChanges.pipe(map(data => filtered(data)))
      .subscribe((data) => {
        this.count = data.count;
        this.nodes = data.nodes;
        this.waitService.setWait(false);
      });
  }

  public routeTo(node): void {
    let node_id = node.id
    let controller_id = ''

    if (this.filter) {
      controller_id = this.filter['controller_id']
    } else {
      controller_id = node.controller.id;
    }

    this.router.navigate([`pages/resourses/nodes/${controller_id}/${node_id}`]);
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
    this.service.paramsForGetNodes.spin = param.spin;
    this.service.paramsForGetNodes.nameSort = param.nameSort;
    this.getNodes();
  }

  ngOnDestroy() {
    this.service.paramsForGetNodes.spin = true;
    this.service.paramsForGetNodes.nameSort = undefined;

    if (this.sub) {
      this.sub.unsubscribe();
    }

    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }
  }

}
