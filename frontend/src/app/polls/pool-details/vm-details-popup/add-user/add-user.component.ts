import { PoolsService } from './../../../pools.service';
import { WaitService } from './../../../../common/components/wait/wait.service';
import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog } from '@angular/material';

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
  selector: 'vdi-add-user-vm',
  templateUrl: './add-user.component.html'
})

export class AddUserVmComponent   {

  private user: string = "";

  constructor(private waitService: WaitService,
              private poolsService: PoolsService,
              @Inject(MAT_DIALOG_DATA) public data: IVmDetails,
              public dialog: MatDialog
            ) {}

  ngOnInit() {
    console.log(this.data);
  }

  public send() {
    this.waitService.setWait(true);
    this.poolsService.assignVmToUser(this.data.vm.id, this.user).subscribe(() => {
      this.poolsService.getPool(this.data.pool_id, this.data.pool_type).subscribe(() => {
        this.waitService.setWait(false);
      });
      this.dialog.closeAll();
    });
  }

  public selectUser(value: []) {
    this.user = value['value'];
  }

}
