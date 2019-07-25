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


  public spinner:boolean = false;

  constructor(private service: ControllersService,public dialog: MatDialog){}

  ngOnInit() {
    this.getAllControllers();
  }

  private getAllControllers() {
    this.spinner = true;
    this.service.getAllControllers().valueChanges.pipe(map(data => data.data.controllers))
      .subscribe((data) => {
        this.controllers = data;
        this.spinner = false;
      },
      (error) => {
        this.spinner = false;
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
