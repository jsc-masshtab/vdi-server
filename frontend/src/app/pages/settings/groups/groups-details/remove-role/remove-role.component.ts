
import { Component, Inject, OnDestroy } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { WaitService } from '../../../../../core/components/wait/wait.service';
import { GroupsService } from '../../groups.service';

@Component({
  selector: 'vdi-remove-role',
  templateUrl: './remove-role.component.html'
})

export class RemoveRoleComponent implements OnDestroy {

  public pending: boolean = false;
  public roles: [] = [];
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  constructor(
    private service: GroupsService,
    private waitService: WaitService,
    private dialogRef: MatDialogRef<RemoveRoleComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any
  ) {}

  public send() {
    if (this.roles.length) {
      this.waitService.setWait(true);
      this.service.removeGroupRole(this.roles, this.data.id).pipe(takeUntil(this.destroy)).subscribe((res) => {
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
    this.roles = value['value'];
    this.valid = true;
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
