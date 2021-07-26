import { Component, OnInit, OnDestroy } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';
import { IParams } from 'types';

import { WaitService } from '../../../core/components/wait/wait.service';
import { ThinClientsService } from '../thin-clients.service';

@Component({
  selector: 'vdi-thin-client-statistic',
  templateUrl: './thin-client-statistic.component.html',
  styleUrls: ['./thin-client-statistic.component.scss']
})
export class ThinClientStatisticComponent implements OnInit, OnDestroy {

  private sub: Subscription;

  public limit = 100;
  public count = 0;
  public offset = 0;

  public data: [];

  public collection: object[] = [
    {
      title: 'Событие',
      property: 'message',
      class: 'name-start',
      icon: 'comment',
      type: 'string',
      sort: true
    },
    {
      title: 'Время подключения',
      property: 'created',
      type: 'time',
      class: 'name-end',
      sort: true
    }
  ];

  constructor(
    private service: ThinClientsService,
    public dialog: MatDialog,
    private waitService: WaitService
  ) { }

  ngOnInit() {
    this.refresh();
  }

  public refresh(): void {
    this.service.params.spin = true;
    this.getStatictic();
  }

  public getStatictic() {
    if (this.sub) {
      this.sub.unsubscribe();
    }

    const queryset = {};

    this.waitService.setWait(true);

    this.service.getThinClientStatistic(queryset).valueChanges.pipe(map(data => data.data.thin_clients_statistics))
      .subscribe((data) => {
        this.data = data;
        this.waitService.setWait(false);
      });
  }

  public sortList(param: IParams): void {
    this.service.params.spin = param.spin;
    this.service.params.nameSort = param.nameSort;
    this.getStatictic();
  }

  public toPage(message: any): void {
    this.offset = message.offset;
    this.getStatictic();
  }

  ngOnDestroy() {
    this.service.params.spin = true;
    this.service.params.nameSort = undefined;

    if (this.sub) {
      this.sub.unsubscribe();
    }
  }
}
