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
  selector: 'vdi-remove-users-pool',
  templateUrl: './remove-users.component.html'
})

export class RemoveUsersPoolComponent  implements OnInit, OnDestroy {

  public pendingUsers: boolean = false;
  public users: [] = [];
  private idUsers: [] = [];
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  constructor(
    private waitService: WaitService,
    private poolService: PoolDetailsService,
    private dialogRef: MatDialogRef<RemoveUsersPoolComponent>,
    @Inject(MAT_DIALOG_DATA) public data: IData
  ) {}

  ngOnInit() {
    this.getUsersToPool();
  }

  public send() {
    if (this.idUsers.length) {
      this.waitService.setWait(true);
      this.poolService.removeUserEntitlementsFromPool(this.data.idPool, this.idUsers).pipe(takeUntil(this.destroy)).subscribe((res) => {
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

  private getUsersToPool() {
    this.pendingUsers = true;
    this.poolService.getAllUsersEntitleToPool(this.data.idPool).pipe(takeUntil(this.destroy))
    .subscribe( (data) => {
      this.users = data.filter(e => !e.is_superuser);
      this.pendingUsers = false;
    },
    () => {
      this.users = [];
      this.pendingUsers = false;
    });
  }

  public selectUser(value: []) {
    this.idUsers = value['value'];
    this.valid = true;
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }
}
