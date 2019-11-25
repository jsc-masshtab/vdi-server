import { PoolDetailsService } from './../pool-details.service';

import { WaitService } from '../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';
import { map } from 'rxjs/operators';

import { PoolsService } from '../../all-pools/pools.service';

interface IData {
  idPool: number;
  namePool: string;
  idCluster: string;
  idNode: string;
  typePool: string;
  address: string;
}

@Component({
  selector: 'vdi-add-vms-static-pool',
  templateUrl: './add-vms.component.html'
})

export class AddVMStaticPoolComponent implements OnInit {

  public pendingVms: boolean = false;
  public vms: [] = [];
  private idVms: [] = [];

  constructor(private poolService: PoolDetailsService,
              private poolsService: PoolsService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<AddVMStaticPoolComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData) { }

  ngOnInit() {
    this.getVms();
  }

  public send() {
    this.waitService.setWait(true);
    this.poolService.addVMStaticPool(this.data.idPool, this.idVms).subscribe(() => {
      this.poolService.getPool(this.data.idPool, this.data.typePool, this.data.address).subscribe(() => {
        this.waitService.setWait(false);
      });
      this.dialogRef.close();
      this.poolsService.paramsForGetPools.spin = false;
      this.poolsService.getAllPools().subscribe();
    });
  }

  private getVms() {
    this.pendingVms = true;
    this.poolService.getAllVms(this.data.idCluster, this.data.idNode).valueChanges.pipe(map((data: any) => data.data.list_of_vms))
      .subscribe((data) => {
        this.vms = data;
        this.pendingVms = false;
      },
      () => {
        this.vms = [];
        this.pendingVms = false;
      });
  }

  public selectVm(value: []) {
    this.idVms = value['value'];
  }

}
