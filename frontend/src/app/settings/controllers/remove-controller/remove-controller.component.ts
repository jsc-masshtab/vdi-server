import { MatDialogRef } from '@angular/material';
import { Component, OnInit } from '@angular/core';
import { ControllersService } from '../controllers.service';
import { map } from 'rxjs/operators';


@Component({
  selector: 'vdi-remove-controller',
  templateUrl: './remove-controller.component.html'
})

export class RemoveControllerComponent implements OnInit {

  public controller: string;
  public description: string;
  public controllers: [];
  public defaultDataControllers:string = "- Загрузка контроллеров -";
  private deleteController:string;


  constructor(private service: ControllersService,
              private dialogRef: MatDialogRef<RemoveControllerComponent>) {}

    
  ngOnInit() {
    this.getAllControllers();
  }

  public send() {
    this.service.removeController(this.deleteController).subscribe((res) => {
      if(res) {
        this.service.getAllControllers().valueChanges.subscribe();
        this.dialogRef.close();
      }
    },(error) => {
      this.dialogRef.close();
    });
  }

  private getAllControllers() {
    this.defaultDataControllers = "- Загрузка контроллеров -";
    this.service.getAllControllers().valueChanges.pipe(map(data => data.data.controllers))
      .subscribe((data) => {
        this.controllers = data.map((item) => {
          return {
            'output': item.ip,
            'input': item.ip
          }
        });
        this.defaultDataControllers = "- нет доступных контроллеров -";
       
      },
      (error) => {
        this.defaultDataControllers = "- нет доступных контроллеров -";
      });
  }

  public selectValue(data) {
    this.deleteController = data[0];
  }

}
