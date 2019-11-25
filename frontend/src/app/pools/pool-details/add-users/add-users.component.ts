import { PoolsService } from './../../all-pools/pools.service';
import { PoolDetailsService } from '../pool-details.service';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';
import { map } from 'rxjs/operators';

interface IData {
  idPool: number;
  namePool: string;
  typePool: string;
  address: string;
}

@Component({
  selector: 'vdi-add-users-pool',
  templateUrl: './add-users.component.html'
})

export class AddUsersPoolComponent implements OnInit {

  public pendingUsers: boolean = false;
  public users: [] = [];
  private idUsers: [] = [];

  constructor(private waitService: WaitService,
              private poolService: PoolDetailsService,
              private poolsService: PoolsService,
              private dialogRef: MatDialogRef<AddUsersPoolComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData
  ) { }

  ngOnInit() {
    this.getUsers();
  }

  public send() {
    this.waitService.setWait(true);
    this.poolService.entitleUsersToPool(this.data.idPool, this.idUsers).subscribe(() => {
      this.poolService.getPool(this.data.idPool, this.data.typePool, this.data.address).subscribe(() => {
        this.poolsService.paramsForGetPools.spin = false;
        this.poolsService.getAllPools().subscribe();
        this.waitService.setWait(false);
      });
      this.dialogRef.close();
    });
  }

  private getUsers() {
    this.pendingUsers = true;
    this.poolService.getAllUsersNoEntitleToPool(this.data.idPool).valueChanges.pipe(map((data: any) => data.data.pool.users))
      .subscribe((data) => {
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
  }

}
