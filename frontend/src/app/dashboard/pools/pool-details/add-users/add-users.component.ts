import { PoolsUpdateService } from './../../all-pools/pools.update.service';
import { PoolDetailsService } from '../pool-details.service';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject, OnInit, OnDestroy } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';
import { takeUntil } from 'rxjs/operators';
import { Subject } from 'rxjs';

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

  constructor(private waitService: WaitService,
              private poolService: PoolDetailsService,
              private dialogRef: MatDialogRef<AddUsersPoolComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData,
              private updatePools: PoolsUpdateService
  ) { }

  ngOnInit() {
    this.getUsers();
  }

  public send() {
    this.waitService.setWait(true);
    this.poolService.entitleUsersToPool(this.data.idPool, this.idUsers).pipe(takeUntil(this.destroy)).subscribe(() => {
      this.poolService.getPool(this.data.idPool, this.data.typePool).pipe(takeUntil(this.destroy)).subscribe(() => {
        this.updatePools.setUpdate('update');
        this.waitService.setWait(false);
        this.dialogRef.close();
      });
    });
  }

  private getUsers() {
    this.pendingUsers = true;
    this.poolService.getAllUsersNoEntitleToPool(this.data.idPool).pipe(takeUntil(this.destroy))
      .subscribe((data) => {
        this.users = data;
        this.pendingUsers = false;
      },
      () => {
        this.users = [];
        this.pendingUsers = false;
      });
  }

  public selectUser(value: string[]) {
    this.idUsers = value['value'];
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
