import { Component, OnDestroy, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { WaitService } from '../../../core/components/wait/wait.service';
import { ControllersService } from '../all-controllers/controllers.service';


interface IData {
  id: string;
  verbose_name: string;
}

@Component({
  selector: 'vdi-remove-controller',
  templateUrl: './remove-controller.component.html'
})

export class RemoveControllerComponent implements OnDestroy {

  private destroy: Subject<any> = new Subject<any>();

  constructor(private controllerService: ControllersService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemoveControllerComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData,
              private router: Router) {}


  public send() {
    this.waitService.setWait(true);
    this.controllerService.removeController(this.data.id).subscribe((res) => {
      if (res) {
        this.controllerService.getAllControllers().valueChanges.pipe(takeUntil(this.destroy)).subscribe(() => {
          this.waitService.setWait(false);
          this.dialogRef.close();
          this.router.navigateByUrl('/pages/controllers');
        });
      }
    });
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
