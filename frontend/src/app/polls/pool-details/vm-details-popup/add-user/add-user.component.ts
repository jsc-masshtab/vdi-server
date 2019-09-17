import { WaitService } from './../../../../common/components/wait/wait.service';
import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { PoolsService } from 'src/app/polls/pools.service';


@Component({
  selector: 'vdi-add-user-vm',
  templateUrl: './add-user.component.html'
})

export class AddUserVmComponent   {

  private user: string = "";

  constructor(private waitService: WaitService,
              private poolsService: PoolsService,
              @Inject(MAT_DIALOG_DATA) public data: any,
              private dialogRef: MatDialogRef<AddUserVmComponent>
            ) {}


  public send() {
    console.log(this.data);
    this.waitService.setWait(true);
    this.poolsService.assignVmToUser(this.data.data.vm.id, this.user).subscribe(() => {
      this.poolsService.getPool(this.data.data.pool_id, this.data.data.pool_type).subscribe(() => {
        this.waitService.setWait(false);
      });
      this.dialogRef.close();
    });
  }


  public selectUser(value:[]) {
    this.user = value['value'];
  }

}
