import { Component, Inject, OnInit, OnDestroy } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { WaitService } from '../../../../core/components/wait/wait.service';
import { PoolDetailsService } from '../pool-details.service';

interface IData {
  idPool: number;
  namePool: string;
  idResourcePool: string;
  idController: string;
  typePool: string;
}

@Component({
  selector: 'vdi-add-vms-static-pool',
  templateUrl: './add-vms.component.html'
})

export class AddVMStaticPoolComponent implements OnInit, OnDestroy {

  public pendingVms: boolean = false;
  public vms: [] = [];
  private vmsInput: [] = [];
  private destroy: Subject<any> = new Subject<any>();

  constructor(
    private poolService: PoolDetailsService,
    private waitService: WaitService,
    private dialogRef: MatDialogRef<AddVMStaticPoolComponent>,
    @Inject(MAT_DIALOG_DATA) public data: IData
  ) {}

  ngOnInit() {
    this.getVms();
  }

  public send() {
    this.waitService.setWait(true);
    this.poolService.addVMStaticPool(this.data.idPool, this.vmsInput).pipe(takeUntil(this.destroy)).subscribe((res) => {
      if (res) {
        this.poolService.getPool(this.data.idPool, this.data.typePool).refetch();
        this.waitService.setWait(false);
        this.dialogRef.close();
      }
    });
  }

  private getVms() {
    this.pendingVms = true;
    this.poolService.getAllVms(this.data.idController, this.data.idResourcePool).pipe(takeUntil(this.destroy))
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
    this.vmsInput = value['value'].map((vm) => ({
        id: vm.id,
        verbose_name: vm.verbose_name
      }));
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }
}