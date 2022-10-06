import { Component, Inject, OnDestroy } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { WaitService } from '@core/components/wait/wait.service';

import { GroupsService } from '../groups.service';

@Component({
  selector: 'vdi-remove-group-permission',
  templateUrl: './remove-permission.component.html'
})
export class RemovePermissionComponent implements OnDestroy {

  public pending: boolean = false;
  public permissions: [] = [];
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  constructor(private service: GroupsService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemovePermissionComponent>,
              @Inject(MAT_DIALOG_DATA) public data: any
  ) {}

  public send() {
    if (this.permissions.length) {
      this.waitService.setWait(true);
      this.service.removePermission(this.data.id, this.permissions).pipe(takeUntil(this.destroy)).subscribe((res) => {
        if (res) {
          this.service.getGroup(this.data.id, this.data.queryset).refetch()
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
