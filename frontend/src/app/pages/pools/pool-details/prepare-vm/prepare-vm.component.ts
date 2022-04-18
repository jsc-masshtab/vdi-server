import { Component, Inject, OnInit, OnDestroy } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { WaitService } from '@core/components/wait/wait.service';
import { PoolDetailsService } from '../pool-details.service';

interface IData {
  idPool: number;
  namePool: string;
  idResourcePool: string;
  idController: string;
  typePool: string;
  vms: [];
}

@Component({
  selector: 'vdi-prepare-vm-pool',
  templateUrl: './prepare-vm.component.html'
})

export class PrepareVmPoolComponent implements OnInit, OnDestroy {

  public pendingVms: boolean = false;
  public vms: [] = [];
  private vmId: string;
  private destroy: Subject<any> = new Subject<any>();

  constructor(
    private poolService: PoolDetailsService,
    private waitService: WaitService,
    private dialogRef: MatDialogRef<PrepareVmPoolComponent>,
    @Inject(MAT_DIALOG_DATA) public data: IData
  ) {}

  ngOnInit() {
    this.getVms();
  }

  public send() {
    this.waitService.setWait(true);
    this.poolService.prepareVm(this.vmId).pipe(takeUntil(this.destroy)).subscribe((res) => {
      if (res) {
        this.poolService.getPool(this.data.idPool).refetch();
        this.waitService.setWait(false);
        this.dialogRef.close();
      }
    });
  }

  private getVms() {
    this.vms = this.data.vms;
  }

  public selectVm(value: any) {
    this.vmId = value['value'].id;
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
