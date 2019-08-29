import { WaitService } from './../../common/components/wait/wait.service';
import { Component, OnInit } from '@angular/core';
import { ControllersService   } from './controllers.service';
import { map } from 'rxjs/operators';
import { MatDialog } from '@angular/material';
import { AddControllerComponent } from './add-controller/add-controller.component';
import { RemoveControllerComponent } from './remove-controller/remove-controller.component';

@Component({
  selector: 'vdi-servers',
  templateUrl: './controllers.component.html'
})


export class ControllersComponent implements OnInit {

  public controllers: [];
  public collection: object[] = [
      {
        title: 'IP адрес',
        property: 'ip',
        class: 'name-start'
      },
      {
        title: 'Описание',
        property: "description"
      }
  ];

  constructor(private service: ControllersService,public dialog: MatDialog,private waitService: WaitService){}

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

  public removeController() { // подумать об общей хранилке
    this.dialog.open(RemoveControllerComponent, {
      width: '500px'
    });
  }

}
