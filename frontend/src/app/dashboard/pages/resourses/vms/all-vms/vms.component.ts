import { Component, OnInit, ViewChild, ElementRef, OnDestroy, Input } from '@angular/core';
import { VmsService } from './vms.service';
import { map } from 'rxjs/operators';
import { WaitService } from '../../../../core/components/wait/wait.service';
import { Router } from '@angular/router';
import { DetailsMove } from 'src/app/dashboard/common/classes/details-move';
import { Subscription } from 'rxjs';
import { IParams } from 'types';
import {FormControl} from '@angular/forms';
import { WebsocketService } from 'src/app/dashboard/common/classes/websock.service';

@Component({
  selector: 'vdi-vms',
  templateUrl: './vms.component.html',
  styleUrls: ['./vms.component.scss']
})


export class VmsComponent extends DetailsMove implements OnInit, OnDestroy {

  @Input() filter: object

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

  public getAllVms() {
    if (this.sub) {
      this.sub.unsubscribe();
    }

    const queryset = {
      user_power_state: this.user_power_state.value
    };

    if (this.user_power_state.value === false) {
      delete queryset['user_power_state'];
    }

    this.waitService.setWait(true);

    let filtered = (data) => {
      if (this.filter) {
        return data.data.controller.vms
      } else {
        return data.data.vms
      }
    }

    this.sub = this.service.getAllVms(this.filter).valueChanges.pipe(map(data => filtered(data))).subscribe((data) => {
      this.vms = data;
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
