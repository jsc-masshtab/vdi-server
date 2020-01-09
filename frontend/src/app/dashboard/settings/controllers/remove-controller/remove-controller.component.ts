import { FormBuilder, FormGroup, Validators } from '@angular/forms';
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
  private destroy: Subject<any> = new Subject<any>();
  public formRemove: FormGroup;
  public valid: boolean = true;

  constructor(private controllerService: ControllersService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemoveControllerComponent>,
              private fb: FormBuilder) {}

  ngOnInit() {
    this.createFormRemove();
    this.getAllControllers();
  }

  private createFormRemove(): void {
    this.formRemove = this.fb.group({
      id: ['', Validators.required],
      full: false
    });
  }

  private checkValid(): boolean {
    if (this.formRemove.status === 'INVALID') {
      this.valid = false;
      return false;
    }
    this.valid = true;
    return true;
  }

  public send() {
    this.checkValid();
    this.waitService.setWait(true);
    this.controllerService.removeController(this.formRemove.value).subscribe((res) => {
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
      });
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
