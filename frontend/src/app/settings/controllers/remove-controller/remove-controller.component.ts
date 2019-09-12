import { WaitService } from './../../../common/components/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, OnInit } from '@angular/core';
import { ControllersService } from '../controllers.service';
import { map } from 'rxjs/operators';


@Component({
  selector: 'vdi-remove-controller',
  templateUrl: './remove-controller.component.html'
})

export class RemoveControllerComponent implements OnInit {

  public controllers: [];
  public pendingControllers: boolean = false;
  private deleteController:string;

  constructor(private controllerService: ControllersService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemoveControllerComponent>) {}

  ngOnInit() {
    this.getAllControllers();
  }

  public send() {
    this.waitService.setWait(true);
    this.controllerService.removeController(this.deleteController).subscribe(() => {
      this.controllerService.getAllControllers().valueChanges.subscribe(() => {
        this.waitService.setWait(false);
      });
      this.dialogRef.close();
    },(error) => {
      this.dialogRef.close();
    });
  }

  private getAllControllers() {
    this.pendingControllers = true;
    this.controllerService.getAllControllers().valueChanges.pipe(map(data => data.data.controllers))
      .subscribe((data) => {
        this.controllers = data;
        this.pendingControllers = false;
      },
      (error) => {
        this.pendingControllers = false;
        this.controllers = [];
      });
  }

  public selectController(value: object) {
    this.deleteController = value['value'];
  }

}
