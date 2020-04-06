import { Router } from '@angular/router';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material';
import { Component, OnDestroy, Inject } from '@angular/core';
import { ControllersService } from '../all-controllers/controllers.service';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

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
  public full: boolean = true;

  constructor(private controllerService: ControllersService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemoveControllerComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData,
              private router: Router) {}


  public send() {
    this.waitService.setWait(true);
    this.controllerService.removeController(this.data.id, this.full).subscribe((res) => {
      if (res) {
        this.controllerService.getAllControllers().valueChanges.pipe(takeUntil(this.destroy)).subscribe(() => {
          this.waitService.setWait(false);
          this.dialogRef.close();
          this.router.navigateByUrl('/pages/settings/controllers');
        });
      }
    });
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
