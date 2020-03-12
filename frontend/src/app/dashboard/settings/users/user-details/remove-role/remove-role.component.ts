import { UsersService } from '../../users.service';

import { WaitService } from '../../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject, OnDestroy } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface IData {
  id: string;
  verbose_name: string;
  roles: string[]; // роли группы
}

@Component({
  selector: 'vdi-remove-role',
  templateUrl: './remove-role.component.html'
})

export class RemoveRoleComponent implements OnDestroy {

  public pending: boolean = false;
  public roles: [] = [];
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  constructor(private service: UsersService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemoveRoleComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData) { }



  public send() {
    if (this.roles.length) {
      this.waitService.setWait(true);
      this.service.removeRole(this.data.id, this.roles).pipe(takeUntil(this.destroy)).subscribe((res) => {
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
    this.roles = value['value'];
    this.valid = true;
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
