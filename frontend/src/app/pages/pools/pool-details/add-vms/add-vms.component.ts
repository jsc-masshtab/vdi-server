import { Component, Inject, OnInit, OnDestroy } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Observable, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { WaitService } from '@core/components/wait/wait.service';
import { PoolDetailsService } from '../pool-details.service';
import { FormControl } from '@angular/forms';

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
  public vms$: Observable<[]>;
  public vmsInput = new FormControl();

  private destroy$: Subject<any> = new Subject<any>();

  constructor(
    private poolService: PoolDetailsService,
    private waitService: WaitService,
    private dialogRef: MatDialogRef<AddVMStaticPoolComponent>,
    @Inject(MAT_DIALOG_DATA) public data: IData
  ) {}

  ngOnInit() {
    this.vms$ = this.poolService.getAllVms(this.data.idController, this.data.idResourcePool);
  }

  public send() {
    const selectedVms = this.vmsInput.value;
    this.waitService.setWait(true);
    this.poolService.addVMStaticPool(this.data.idPool, selectedVms ).pipe(takeUntil(this.destroy$)).subscribe((res) => {
      if (res) {
        this.poolService.getPool(this.data.idPool).refetch();
        this.waitService.setWait(false);
        this.dialogRef.close();
      }
    });
  }


  public selectAllVms(vms: []): void { 
    this.vmsInput.setValue(vms);
  }

  public deselectAllVms(){
    this.vmsInput.setValue([]);
  }
  ngOnDestroy() {    
    this.destroy$.next();
  }
}
