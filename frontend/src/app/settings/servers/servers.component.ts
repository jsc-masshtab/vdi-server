import { Component, OnInit } from '@angular/core';
import { ServersService   } from './servers.service';
import { map } from 'rxjs/operators';
import { MatDialog } from '@angular/material';
import { AddControllerComponent } from './add-controller/add-controller.component';

@Component({
  selector: 'vdi-servers',
  templateUrl: './servers.component.html',
  styleUrls: ['./servers.component.scss']
})


export class ServersComponent implements OnInit {

  public controllers: [];;
  public collection: object[] = [];
  public crumbs: object[] = [
    {
      title: 'Настройки',
      icon: 'cog'
    },
    {
      title: 'Контроллеры',
      icon: 'server'
    }
  ];

  public spinner:boolean = true;


  constructor(private service: ServersService,public dialog: MatDialog){}

  ngOnInit() {
    this.collectionAction();
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
        this.spinner = false;
      },
      (error) => {
        this.spinner = false;
      });
  }

  public collectionAction(): void {
    this.collection = [
      {
        title: 'IP адрес',
        property: 'ip'
      },
      {
        title: 'Описание',
        property: "description"
      }
    ];
  }

  public addController() {
    this.dialog.open(AddControllerComponent, {
      width: '500px'
    });
  }

}
