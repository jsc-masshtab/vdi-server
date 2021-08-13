
import { Component, Inject, OnDestroy } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { WaitService } from '../../../../../core/components/wait/wait.service';
import { GroupsService } from '../../groups.service';

interface IData {
  id: string;
  verbose_name: string;
  users: string[]; // юзеры группы
}

@Component({
  selector: 'vdi-remove-user',
  templateUrl: './remove-user.component.html'
})

export class RemoveUserGroupComponent implements OnDestroy {

  public pending: boolean = false;
  public users: [] = [];
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  constructor(private service: GroupsService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemoveUserGroupComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData) { }



  public send() {
    if (this.users.length) {
      this.waitService.setWait(true);
      this.service.removeUsers(this.users, this.data.id).pipe(takeUntil(this.destroy)).subscribe((res) => {
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
    this.users = value['value'];
    this.valid = true;
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
