import { Component, OnInit, ViewChild, ElementRef, OnDestroy, Input } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';

import { WaitService } from '@core/components/wait/wait.service';
import { DetailsMove } from '@shared/classes/details-move';
import { IParams } from '@shared/types';
import { DatapoolsService } from './datapools.service';
import { WebsocketService } from '@app/core/services/websock.service';


@Component({
  selector: 'vdi-datapools',
  templateUrl: './datapools.component.html',
  styleUrls: ['./datapools.component.scss']
})


export class DatapoolsComponent extends DetailsMove implements OnInit, OnDestroy {

  @Input() filter: object

  public refresh: boolean = false

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
      title: 'Свободно',
      property: 'free_space',
      type: 'bites',
      delimiter: 'Мб',
      sort: true
    },
    {
      title: 'Занято',
      property: 'used_space',
      type: 'bites',
      delimiter: 'Мб',
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
  private socketSub: Subscription;

  constructor(
    private service: DatapoolsService,
    private waitService: WaitService,
    private router: Router,
    private ws: WebsocketService
  ) {
    super();
  }

  @ViewChild('view', { static: true }) view: ElementRef;

  ngOnInit() {
    this.getDatapools();
    this.listenSockets();
  }

  private listenSockets() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }

    this.socketSub = this.ws.stream('/data-pools/').subscribe((message: any) => {
      if (message['msg_type'] === 'data') {
        this.service.getAllDatapools(this.filter).refetch();
      }
    });
  }

  public getDatapools(refresh?) {
    if (this.sub) {
      this.sub.unsubscribe();
    }
    this.waitService.setWait(true);

    let filtered = (data) => {
      if ((this.filter && !this.refresh) || (this.filter && this.refresh)) {
        return data.data.controller.data_pools
      } else {
        return data.data.datapools
      }
    }

    if (refresh) {
      this.refresh = refresh
    }
    this.sub = this.service.getAllDatapools(this.filter, this.refresh).valueChanges.pipe(map(data => filtered(data)))
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

    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }
  }

}
