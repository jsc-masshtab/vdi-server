import { WaitService } from './../../common/components/wait/wait.service';
import { PoolsService } from '../pools.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';


@Component({
  selector: 'vdi-remove-vms-static-pool',
  templateUrl: './remove-vms.component.html'
})

export class RemoveVMStaticPoolComponent  {

  public pendingVms:boolean = false;
  private id_vms: [] = [];

  constructor(private poolService: PoolsService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemoveVMStaticPoolComponent>,
              @Inject(MAT_DIALOG_DATA) public data: any) {}


 
  public send() {
    this.waitService.setWait(true);
    this.poolService.removeVMStaticPool(this.data.pool_id,this.id_vms).subscribe(() => {
      this.dialogRef.close();
      this.poolService.getPool(this.data.pool_id,this.data.pool_type).subscribe();
      this.waitService.setWait(false);
    });
  }

  public selectVm(value:[]) {
    this.id_vms = value['value'];
  }

}
