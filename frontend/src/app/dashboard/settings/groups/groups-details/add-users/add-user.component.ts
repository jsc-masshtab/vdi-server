import { GroupsService } from './../../groups.service';

import { WaitService } from '../../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface IData {
  id: string;
  verbose_name: string;
  users: string[]; // доступные для добавления в группу
}

@Component({
  selector: 'vdi-add-user',
  templateUrl: './add-user.component.html'
})

export class AddUserGroupComponent implements OnInit, OnDestroy {

  public pending: boolean = false;
  public users: [] = [];
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  public selected_users: string[] = [];

  constructor(private service: GroupsService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<AddUserGroupComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData) { }

  
  ngOnInit() {
    this.selected_users = this.data.users
  }

  public search(name) {
    let filter = String(name).toLowerCase();
    this.selected_users = this.data.users.filter((user: any) => user.username.toLowerCase().startsWith(filter) || this.users.some(selected => selected === user.id))
  }

  public select(value: []) {
    this.users = value['value'];
    this.valid = true;
  }

  public send() {
    if (this.users.length) {
      this.waitService.setWait(true);
      this.service.addUsers(this.users, this.data.id).pipe(takeUntil(this.destroy)).subscribe((res) => {
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

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
