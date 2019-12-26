import { WaitService } from '../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { ControllersService } from '../all-controllers/controllers.service';
import { map } from 'rxjs/operators';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';


@Component({
  selector: 'vdi-remove-controller',
  templateUrl: './remove-controller.component.html'
})

export class RemoveControllerComponent implements OnInit, OnDestroy {

  public controllers: [];
  public pendingControllers: boolean = false;
  private deleteController: string;
  private destroy: Subject<any> = new Subject<any>();

  constructor(private controllerService: ControllersService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemoveControllerComponent>) {}

  ngOnInit() {
    this.getAllControllers();
  }

  public send() {
    this.waitService.setWait(true);
    this.controllerService.removeController(this.deleteController).subscribe((res) => {
      if (res) {
        this.controllerService.getAllControllers().valueChanges.pipe(takeUntil(this.destroy)).subscribe(() => {
          this.waitService.setWait(false);
          this.dialogRef.close();
        });
      }
    });
  }

  private getAllControllers() {
    this.pendingControllers = true;
    this.controllerService.getAllControllers().valueChanges.pipe(takeUntil(this.destroy), map(data => data.data.controllers))
      .subscribe((data) => {
        this.controllers = data;
        this.pendingControllers = false;
      },
      () => {
        this.pendingControllers = false;
        this.controllers = [];
      });
  }

  public selectController(value: object) {
    this.deleteController = value['value'];
  }


  ngOnDestroy() {
    this.destroy.next(null);
  }

}
