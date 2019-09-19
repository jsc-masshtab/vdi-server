import { PoolsService } from './../../../pools.service';
import { WaitService } from './../../../../common/components/wait/wait.service';
import { Component, Inject } from '@angular/core';
import { MatDialog, MAT_DIALOG_DATA } from '@angular/material';

interface IVmDetails  {
  vm: {
    id: number
    name: string
    state: string
  };
  pool_type: string;
  pool_users: [{[key: string]: IPoolUser }];
  pool_id: number;
}

interface IPoolUser {
  username: string;
}

@Component({
  selector: 'vdi-remove-user-vm',
  templateUrl: './remove-user.component.html'
})

export class RemoveUserVmComponent {

  constructor(private waitService: WaitService,
              private poolsService: PoolsService,
              public dialog: MatDialog,
              @Inject(MAT_DIALOG_DATA) public data: IVmDetails,
            ) {}

  public send() {
    this.waitService.setWait(true);
    this.poolsService.freeVmFromUser(this.data.vm.id).subscribe(() => {
      this.poolsService.getPool(this.data.pool_id, this.data.pool_type).subscribe(() => {
        this.waitService.setWait(false);
      });
      this.dialog.closeAll();
    });
  }

}
