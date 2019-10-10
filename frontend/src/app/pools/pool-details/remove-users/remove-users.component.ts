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
}

@Component({
  selector: 'vdi-remove-users-pool',
  templateUrl: './remove-users.component.html'
})

export class RemoveUsersPoolComponent  implements OnInit {

  public pendingUsers: boolean = false;
  public users: [] = [];
  private idUsers: [] = [];

  constructor(private waitService: WaitService,
              private poolService: PoolDetailsService,
              private dialogRef: MatDialogRef<RemoveUsersPoolComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData
             ) {}

  ngOnInit() {
    this.getUsersToPool();
  }

  public send() {
    this.waitService.setWait(true);
    this.poolService.removeUserEntitlementsFromPool(this.data.idPool, this.idUsers).subscribe(() => {
      this.poolService.getPool({id: this.data.idPool, type: this.data.typePool}).subscribe(() => {
        this.waitService.setWait(false);
      });
      this.dialogRef.close();
    });
  }

  private getUsersToPool() {
    this.pendingUsers = true;
    this.poolService.assesUsersToPool(this.data.idPool).valueChanges.pipe(map((data: any) => data.data.pool.users))
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
  }
}
