import { Component, OnInit } from '@angular/core';
import { ControllersService   } from './controllers.service';
import { map } from 'rxjs/operators';
import { MatDialog } from '@angular/material';
import { AddControllerComponent } from './add-controller/add-controller.component';
import { RemoveControllerComponent } from './remove-controller/remove-controller.component';

@Component({
  selector: 'vdi-servers',
  templateUrl: './controllers.component.html',
  styleUrls: ['./controllers.component.scss']
})


export class ControllersComponent implements OnInit {

  public controllers: [];
  public collection: object[] = [
      {
        title: 'IP адрес',
        property: 'ip'
      },
      {
        title: 'Описание',
        property: "description"
      }
  ];
  public crumbs: object[] = [
    {
      title: 'Настройки',
      icon: 'cog'
    }
  ];

  public spinner:boolean = true;

  constructor(private service: ControllersService,public dialog: MatDialog){}

  ngOnInit() {
    this.getAllControllers();
  }

  private getAllControllers() {
    this.service.getAllControllers().valueChanges.pipe(map(data => data.data.controllers))
      .subscribe((data) => {
        this.controllers = data;
        localStorage.removeItem('controller');
        if(this.controllers.length) {
          localStorage.setItem('controller',JSON.stringify(data[0].ip));
        }
        this.crumbs.push({
          title: 'Контроллеры',
          icon: 'server'
        });
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
