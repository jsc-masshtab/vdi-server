import { Component, OnInit, ViewChild, ElementRef, OnDestroy, Input } from '@angular/core';
import {FormControl} from '@angular/forms';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';

import { WaitService } from '@core/components/wait/wait.service';
import { DetailsMove } from '@shared/classes/details-move';
import { IParams } from '@shared/types';
import { VmsService } from './vms.service';
import { WebsocketService } from '@app/core/services/websock.service';

@Component({
  selector: 'vdi-vms',
  templateUrl: './vms.component.html',
  styleUrls: ['./vms.component.scss']
})
export class VmsComponent extends DetailsMove implements OnInit, OnDestroy {

  @Input() filter: object

  public limit = 100;
  public count = 0;
  public offset = 0;
  public queryset: any;

  public refresh: boolean = false

  private sub: Subscription;
  private socketSub: Subscription;

  user_power_state = new FormControl('all');

  public vms: object[] = [];
  public collection = [
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
      type: 'string',
      sort: true
    },
    {
      title: 'Пул',
      property: 'pool_name',
      type: 'string',
      sort: true
    },
    {
      title: 'Статус',
      property: 'status',
      sort: true
    }
  ];

  constructor(
    private service: VmsService,
    private waitService: WaitService,
    private router: Router,
    private ws: WebsocketService
  ) {
    super();
  }

  @ViewChild('view', { static: true }) view: ElementRef;

  ngOnInit() {
    this.getAllVms();
    this.listenSockets();

    this.user_power_state.valueChanges.subscribe(() => {
      this.getAllVms();
    })
  }

  private listenSockets() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }

    this.socketSub = this.ws.stream('/domains/').subscribe((message: any) => {
      if (message['msg_type'] === 'data') {
        this.service.getAllVms(this.filter).refetch();
      }
    });
  }

  public toPage(message: any): void {
    this.offset = message.offset;
    this.getAllVms();
  }

  public getAllVms(refresh?) {
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
        return data.data.vms_with_count
      }
    }

    if (refresh) {
      this.refresh = refresh
    }

    this.sub = this.service.getAllVms({
      ...this.filter,
      ...queryset
    }, this.refresh).valueChanges.pipe(map(data => filtered(data))).subscribe((data) => {
      this.count = data.count;
      this.vms = data.vms;
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
    let id = event.id
    let controller_id = ''

    if (this.filter) {
      controller_id = this.filter['controller_id']
    } else {
      controller_id = event.controller.id;
    }

    this.router.navigate([`pages/resourses/vms/${controller_id}/${id}`]);
  }

  public sortList(param: IParams): void {
    this.service.params.spin = param.spin;
    this.service.params.nameSort = param.nameSort;
    this.getAllVms();
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }

    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }
  }
}
