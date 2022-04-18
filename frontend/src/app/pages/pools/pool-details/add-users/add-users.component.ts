import { Component, Inject, OnInit, OnDestroy } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { WaitService } from '../../../../core/components/wait/wait.service';
import { PoolDetailsService } from '../pool-details.service';

interface IData {
  idPool: string;
  namePool: string;
  typePool: string;
}

@Component({
  selector: 'vdi-add-users-pool',
  templateUrl: './add-users.component.html'
})

export class AddUsersPoolComponent implements OnInit, OnDestroy {

  public pendingUsers: boolean = false;
  public users: [] = [];
  private idUsers: [] = [];
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  public selected_users: string[] = [];

  constructor(private waitService: WaitService,
              private poolService: PoolDetailsService,
              private dialogRef: MatDialogRef<AddUsersPoolComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData
  ) { }

  ngOnInit() {
    this.getUsers();
  }


  public search(name) {
    let filter = String(name).toLowerCase();
    this.selected_users = this.users.filter(
      (user: any) => user.username.toLowerCase().startsWith(filter) || this.idUsers.some(selected => selected === user.id)
    );
  }

  public send() {
    if (this.idUsers.length) {
      this.waitService.setWait(true);
      this.poolService.entitleUsersToPool(this.data.idPool, this.idUsers).pipe(takeUntil(this.destroy)).subscribe((res) => {
        if (res) {
          this.poolService.getPool(this.data.idPool).refetch();
          this.waitService.setWait(false);
          this.dialogRef.close();
        }
      });
    } else {
      this.valid = false;
    }
  }

  private getUsers() {
    this.pendingUsers = true;
    this.poolService.getAllUsersNoEntitleToPool(this.data.idPool).pipe(takeUntil(this.destroy))
      .subscribe((data) => {
        this.users = data;
        this.selected_users = this.users;
        this.pendingUsers = false;
      },
        () => {
          this.users = [];
          this.pendingUsers = false;
        });
  }

  public selectUser(value: string[]) {
    this.idUsers = value['value'];
    this.valid = true;
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
