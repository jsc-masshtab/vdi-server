import { Component, Inject, OnDestroy } from '@angular/core';
import { Subject } from 'rxjs';
import { UsersService } from '../../users.service';
import { WaitService } from 'src/app/dashboard/common/components/single/wait/wait.service';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'vdi-add-user-permission',
  templateUrl: './add-permission.component.html'
})
export class AddPermissionComponent implements OnDestroy {

  public pending: boolean = false;
  public permissions: [] = [];
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  constructor(private service: UsersService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<AddPermissionComponent>,
              @Inject(MAT_DIALOG_DATA) public data: any
  ) { }

  public send() {
    if (this.permissions.length) {
      this.waitService.setWait(true);
      this.service.addPermission(this.data.id, this.permissions).pipe(takeUntil(this.destroy)).subscribe((res) => {
        if (res) {
          this.service.getUser(this.data.id).refetch();
          this.waitService.setWait(false);
          this.dialogRef.close();
        }
      });
    } else {
      this.valid = false;
    }
  }

  public select(value: []) {
    this.permissions = value['value'];
    this.valid = true;
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
