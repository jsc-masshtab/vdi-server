import { DetailsMove } from './../../../common/classes/details-move';
import { Router } from '@angular/router';
import { IParams } from '../../../../../../types';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { ControllersService } from './controllers.service';
import { map } from 'rxjs/operators';
import { MatDialog } from '@angular/material/dialog';
import { AddControllerComponent } from '../add-controller/add-controller.component';
import { RemoveControllerComponent } from '../remove-controller/remove-controller.component';
import { Subscription } from 'rxjs';
import { WebsocketService } from 'src/app/dashboard/common/classes/websock.service';

@Component({
  selector: 'vdi-servers',
  templateUrl: './controllers.component.html'
})

export class ControllersComponent extends DetailsMove implements OnInit, OnDestroy {

  private socketSub: Subscription;

  public controllers: [];
  public collection: object[] = [
    {
      title: 'Имя контроллера',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'server',
      type: 'string',
      sort: true
    },
    {
      title: 'IP адрес',
      property: 'address',
      type: 'string',
      sort: true
    },
    {
      title: 'Пользователь',
      property: 'username',
      type: 'string',
      sort: true
    },
    {
      title: 'Описание',
      property: 'description',
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
    private service: ControllersService,
    public dialog: MatDialog,
    private waitService: WaitService,
    private router: Router,
    private ws: WebsocketService
  ) {
    super();
  }

  @ViewChild('view', { static: true }) view: ElementRef;

  ngOnInit() {
    this.getAllControllers();
    this.listenSockets()
  }

  private listenSockets() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }

    this.socketSub = this.ws.stream('/controllers/').subscribe((message: any) => {
      if (message['msg_type'] === 'data') {
        this.service.getAllControllers().refetch();
      }
    });
  }

  public getAllControllers() {
    this.waitService.setWait(true);
    this.service.getAllControllers().valueChanges.pipe(map(data => data.data.controllers))
      .subscribe((data) => {
        this.controllers = data;
        this.waitService.setWait(false);
      });
  }

  public addController() {
    this.dialog.open(AddControllerComponent, {
      disableClose: true,
      width: '500px'
    });
  }

  public removeController() {
    this.dialog.open(RemoveControllerComponent, {
      disableClose: true,
      width: '500px'
    });
  }

  public sortList(param: IParams): void  {
    this.service.paramsForGetControllers.spin = param.spin;
    this.service.paramsForGetControllers.nameSort = param.nameSort;
    this.getAllControllers();
  }

  public routeTo(event): void {
    this.router.navigate([`pages/controllers/${event['id']}`]);
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

  ngOnDestroy() {
    this.service.paramsForGetControllers.spin = true;
    this.service.paramsForGetControllers.nameSort = undefined;

    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }
  }
}
