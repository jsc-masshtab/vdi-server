import { PoolsUpdateService } from './../../all-pools/pools.update.service';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { PoolDetailsService } from '../pool-details.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject, OnDestroy } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

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

export class RemoveVMStaticPoolComponent implements OnDestroy {

  private idVms: [] = [];
  private destroy: Subject<any> = new Subject<any>();

  constructor(private poolService: PoolDetailsService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemoveVMStaticPoolComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData,
              private updatePools: PoolsUpdateService) {}

  public send() {
    this.waitService.setWait(true);
    this.poolService.removeVMStaticPool(this.data.idPool, this.idVms).pipe(takeUntil(this.destroy)).subscribe(() => {
      this.poolService.getPool(this.data.idPool, this.data.typePool).pipe(takeUntil(this.destroy)).subscribe(() => {
        this.waitService.setWait(false);
        this.dialogRef.close();
        this.updatePools.setUpdate('update');
        console.log('remove vm');
      });
    });
  }

  public selectVm(value: []) {
    this.idVms = value['value'];
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
