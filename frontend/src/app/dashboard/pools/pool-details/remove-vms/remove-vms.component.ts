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

  constructor(
    private poolService: PoolDetailsService,
    private waitService: WaitService,
    private dialogRef: MatDialogRef<RemoveVMStaticPoolComponent>,
    @Inject(MAT_DIALOG_DATA) public data: IData
  ){}

  public send() {
    this.waitService.setWait(true);

    const method = this.data.typePool == 'static' ? 'removeVMStaticPool' : 'removeVmsDynamicPool'

    this.poolService[method](this.data.idPool, this.idVms).pipe(takeUntil(this.destroy)).subscribe((res) => {
      if (res) {
        this.poolService.getPool(this.data.idPool, this.data.typePool).refetch()
        this.waitService.setWait(false);
        this.dialogRef.close();
      }
    });
  }

  public selectVm(value: []) {
    this.idVms = value['value'];
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
