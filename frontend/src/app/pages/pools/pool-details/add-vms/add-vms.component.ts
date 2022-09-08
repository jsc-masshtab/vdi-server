import { Component, Inject, OnInit, OnDestroy } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Observable, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { trigger, transition, style, animate } from '@angular/animations';

import { WaitService } from '@core/components/wait/wait.service';
import { PoolDetailsService } from '../pool-details.service';
import { FormControl, Validators } from '@angular/forms';

interface IData {
  idPool: number;
  namePool: string;
  idResourcePool: string;
  idController: string;
  typePool: string;
  queryset: any;
}
 
@Component({
  selector: 'vdi-add-vms-static-pool',
  templateUrl: './add-vms.component.html',
  animations: [
    trigger(
      'animForm', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('150ms', style({ opacity: 1 }))
      ]),
      transition(':leave', [
        style({ opacity: 1 }),
        animate('150ms', style({ opacity: 0 }))
      ])
    ])
  ]
})

export class AddVMStaticPoolComponent implements OnInit, OnDestroy {
  
  public pendingVms: boolean = false;
  public checkValid: boolean = false;

  public vms$: Observable<[]>;
  public vmsInput = new FormControl([], Validators.required);

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
    if (!this.vmsInput.valid) {
      this.checkValid = true;
      return;
    }

    const selectedVms = this.vmsInput.value;
    let method = '';

    switch (this.data.typePool) {
      case 'static':
        method = 'addVMStaticPool';
        break;
      case 'rds':
        method = 'addVmsToRdsPool';
        break;
      default:
        return;
    }

    if (method) {

      this.waitService.setWait(true);
      
      this.poolService[method](this.data.idPool, selectedVms).pipe(takeUntil(this.destroy$)).subscribe((res) => {
        if (res) {
          this.poolService.getPool(this.data.idPool, this.data.queryset).refetch();
          this.waitService.setWait(false);
          this.dialogRef.close();
        }
      });
    }
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
