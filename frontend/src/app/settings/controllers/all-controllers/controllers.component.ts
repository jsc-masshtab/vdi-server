import { IParams } from './../../../../../types/index.d';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { ControllersService } from './controllers.service';
import { map } from 'rxjs/operators';
import { MatDialog } from '@angular/material';
import { AddControllerComponent } from '../add-controller/add-controller.component';
import { RemoveControllerComponent } from '../remove-controller/remove-controller.component';

@Component({
  selector: 'vdi-servers',
  templateUrl: './controllers.component.html'
})

export class ControllersComponent implements OnInit, OnDestroy{

  public controllers: [];
  public collection: object[] = [
    {
      title: 'IP адрес',
      property: 'ip',
      class: 'name-start',
      icon: 'building',
      type: 'string',
      reverse_sort: true
    },
    {
      title: 'Описание',
      property: 'description',
      type: 'string',
      reverse_sort: true
    },
    {
      title: 'Статус',
      property: 'status',
      reverse_sort: true
    }
  ];

  constructor(private service: ControllersService, public dialog: MatDialog, private waitService: WaitService) { }

  ngOnInit() {
    this.getAllControllers();
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
      width: '500px'
    });
  }

  public removeController() {
    this.dialog.open(RemoveControllerComponent, {
      width: '500px'
    });
  }

  public sortList(param: IParams): void  {
    this.service.paramsForGetControllers.spin = param.spin;
    this.service.paramsForGetControllers.nameSort = param.nameSort;
    this.service.paramsForGetControllers.reverse = param.reverse;
    this.getAllControllers();
  }

  ngOnDestroy() {
    this.service.paramsForGetControllers.spin = true;
    this.service.paramsForGetControllers.nameSort = undefined;
    this.service.paramsForGetControllers.reverse = undefined;
  }

}
