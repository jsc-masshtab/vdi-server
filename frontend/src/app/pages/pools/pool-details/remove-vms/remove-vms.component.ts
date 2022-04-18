import { Component, Inject, OnDestroy } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { trigger, transition, style, animate } from '@angular/animations';

import { WaitService } from '@core/components/wait/wait.service';
import { PoolDetailsService } from '../pool-details.service';

interface IData {
  idPool: number;
  namePool: string;
  vms: [];
  typePool: string;
}

@Component({
  selector: 'vdi-remove-vms-static-pool',
  templateUrl: './remove-vms.component.html',
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

export class RemoveVMStaticPoolComponent implements OnDestroy {

  
  private destroy: Subject<void> = new Subject<void>();
  public checkValid: boolean = false 
  public form = new FormGroup({
    vmsInput: new FormControl([], Validators.required)
  })
  constructor(
    private poolService: PoolDetailsService,
    private waitService: WaitService,
    private dialogRef: MatDialogRef<RemoveVMStaticPoolComponent>,
    @Inject(MAT_DIALOG_DATA) public data: IData
  ) {}

  public send(): void {
    if (!this.form.valid){
      this.checkValid = true;
      return;
    }
  
    const selectedVms = this.form.get('vmsInput').value;  

    this.waitService.setWait(true);

    const method = this.data.typePool === 'static' ? 'removeVMStaticPool' : 'removeVmsDynamicPool'

    this.poolService[method](this.data.idPool, selectedVms).pipe(takeUntil(this.destroy)).subscribe((res) => {
      if (res) {
        setTimeout( () => this.poolService.getPool(this.data.idPool).refetch(), 500)

        this.waitService.setWait(false);
        this.dialogRef.close();
      }
    });
  }

  public selectAllVms(): void { 
    
    this.form.get('vmsInput').setValue(this.data.vms.map( (vm: any) => vm.id ));
  }

  public deselectAllVms(){
    this.form.get('vmsInput').setValue([]);
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
