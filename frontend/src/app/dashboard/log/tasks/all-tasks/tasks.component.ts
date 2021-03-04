import { TasksService } from './tasks.service';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { map } from 'rxjs/operators';
import { MatDialog } from '@angular/material';
import { InfoTaskComponent } from '../info-tasks/info-tasks.component';
import { FormControl } from '@angular/forms';
import { IParams } from 'types';
import { WebsocketService } from 'src/app/dashboard/common/classes/websock.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'vdi-tasks',
  templateUrl: './tasks.component.html',
  styleUrls: ['./tasks.component.scss']
})

export class TasksComponent implements OnInit, OnDestroy {

  private socketSub: Subscription;

  public limit = 100;
  public count = 0;
  public offset = 0;

  task_type = new FormControl('all');
  status = new FormControl('all');

  public collection: object[] = [
    {
      title: 'Сообщение',
      property: 'message',
      class: 'name-start',
      type: 'string',
      icon: 'gavel'
    },
    {
      title: 'Тип',
      property: 'task_type',
      type: 'string',
      sort: true
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string',
      sort: true
    },
    {
      title: 'Время создания',
      property: 'started',
      type: 'time',
      class: 'name-end',
      sort: true
    },
    {
      title: 'Время завершения',
      property: 'finished',
      type: 'time',
      class: 'name-end',
      sort: true
    }
  ];

  public tasks: object[] = [];

  public queryset: any;

  constructor(
    private service: TasksService,
    private waitService: WaitService,
    public dialog: MatDialog,
    private ws: WebsocketService
  ) { }

  ngOnInit() {
    this.refresh();
    this.listenSockets();

    this.task_type.valueChanges.subscribe(() => {
      this.getTasks();
    });

    this.status.valueChanges.subscribe(() => {
      this.getTasks();
    });
  }

  public refresh(): void {
    this.getTasks();
  }

  public clickRow(task): void {
    this.openTaskDetails(task);
  }

  public toPage(message: any): void {
    this.offset = message.offset;
    this.getTasks();
  }

  public sortList(param: IParams): void {
    this.service.paramsForGetTasks.spin = param.spin;
    this.service.paramsForGetTasks.nameSort = param.nameSort;
    this.getTasks();
  }

  public getTasks(): void {

    const queryset = {
      offset: this.offset,
      limit: this.limit,
      task_type: this.task_type.value,
      status: this.status.value
    };

    if (this.task_type.value === 'all') {
      delete queryset['task_type'];
    }

    if (this.status.value === 'all') {
      delete queryset['status'];
    }

    this.queryset = queryset;

    this.waitService.setWait(true);
    this.service.getAllTasks(queryset).valueChanges.pipe(map(data => data.data))
      .subscribe((data) => {
        this.tasks = [...data.tasks];
        this.count = data.count || 0;
        this.waitService.setWait(false);
      });
  }

  private listenSockets() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }

    this.socketSub = this.ws.stream('/vdi_tasks/').subscribe(() => {
      this.service.getAllTasks(this.queryset).refetch();
    });
  }

  public openTaskDetails(task: any): void {
    this.dialog.open(InfoTaskComponent, {
      disableClose: true,
      width: '700px',
      data: {
        task: { ...task }
      }
    });
  }

  ngOnDestroy() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }
  }
}
