import { PoolsService } from './../../pools.service';
import { WaitService } from './../../../common/components/wait/wait.service';
import { PoolDetailsService } from '../pool-details.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject, OnChanges } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';

interface IData {
  idPool: number;
  namePool: string;
  vms: [];
  typePool: string;
}

@Component({
  selector: 'vdi-remove-vms-static-pool',
  templateUrl: './remove-vms.component.html'
})

export class RemoveVMStaticPoolComponent implements OnChanges {

  public pendingVms: boolean = true;
  private idVms: [] = [];

  constructor(private poolService: PoolDetailsService,
              private poolsService: PoolsService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemoveVMStaticPoolComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData) {}

  ngOnChanges() {
    console.log(this.data);
  }

  public send() {
    this.waitService.setWait(true);
    this.poolService.removeVMStaticPool(this.data.idPool, this.idVms).subscribe(() => {
      this.poolService.getPool(this.data.idPool, this.data.typePool).subscribe(() => {
        this.waitService.setWait(false);
      });
      this.dialogRef.close();
      this.poolsService.getAllPools().subscribe();
    });
  }

  public selectVm(value: []) {
    this.idVms = value['value'];
  }

}
