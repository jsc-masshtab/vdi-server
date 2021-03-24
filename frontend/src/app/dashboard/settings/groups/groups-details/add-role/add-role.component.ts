import { GroupsService } from './../../groups.service';

import { WaitService } from '../../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material/dialog';
import { Component, Inject, OnDestroy } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface IData {
  id: string;
  verbose_name: string;
  roles: string[]; // доступные для группы
}

@Component({
  selector: 'vdi-add-role',
  templateUrl: './add-role.component.html'
})

export class AddRoleComponent implements OnDestroy {

  public pending: boolean = false;
  public roles: [] = [];
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  constructor(private service: GroupsService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<AddRoleComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData) { }



  public send() {
    if (this.roles.length) {
      this.waitService.setWait(true);
      this.service.addGroupRole(this.roles, this.data.id).pipe(takeUntil(this.destroy)).subscribe((res) => {
        if (res) {
          this.service.getGroup(this.data.id).pipe(takeUntil(this.destroy)).subscribe(() => {
            this.waitService.setWait(false);
            this.dialogRef.close();
          });
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
