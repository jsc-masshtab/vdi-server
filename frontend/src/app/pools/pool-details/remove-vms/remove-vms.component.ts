import { PoolsService } from '../../all-pools/pools.service';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { PoolDetailsService } from '../pool-details.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';

interface IData {
  idPool: number;
  namePool: string;
  vms: [];
  typePool: string;
  address: string;
}

@Component({
  selector: 'vdi-remove-vms-static-pool',
  templateUrl: './remove-vms.component.html'
})

export class RemoveVMStaticPoolComponent {

  private idVms: [] = [];

  constructor(private poolService: PoolDetailsService,
              private poolsService: PoolsService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemoveVMStaticPoolComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData) {}

  public send() {
    this.waitService.setWait(true);
    this.poolService.removeVMStaticPool(this.data.idPool, this.idVms).subscribe(() => {
      this.poolService.getPool(this.data.idPool, this.data.typePool, this.data.address).subscribe(() => {
        this.waitService.setWait(false);
      });
      this.dialogRef.close();
      this.poolsService.paramsForGetPools.spin = false;
      this.poolsService.getAllPools().subscribe();
    });
  }

  public selectVm(value: []) {
    this.idVms = value['value'];
  }

}
