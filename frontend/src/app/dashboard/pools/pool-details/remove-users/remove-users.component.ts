import { PoolDetailsService } from '../pool-details.service';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject, OnInit, OnDestroy } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { PoolsUpdateService } from './../../all-pools/pools.update.service';

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

  constructor(private waitService: WaitService,
              private poolService: PoolDetailsService,
              private dialogRef: MatDialogRef<RemoveUsersPoolComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData,
              private updatePools: PoolsUpdateService
             ) {}

  ngOnInit() {
    this.getUsersToPool();
  }

  public send() {
    if (this.idUsers.length) {
      this.waitService.setWait(true);
      this.poolService.removeUserEntitlementsFromPool(this.data.idPool, this.idUsers).pipe(takeUntil(this.destroy)).subscribe((res) => {
        if (res) {
          this.poolService.getPool(this.data.idPool, this.data.typePool).pipe(takeUntil(this.destroy)).subscribe(() => {
            this.updatePools.setUpdate('update');
            this.waitService.setWait(false);
            this.dialogRef.close();
          });
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
      this.users = data;
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
