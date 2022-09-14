import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { debounceTime, map, takeUntil } from 'rxjs/operators';
import { trigger, transition, style, animate } from '@angular/animations';

import { WaitService } from '@core/components/wait/wait.service';
import { PoolDetailsService } from '../pool-details.service';

interface IData {
  idPool: number;
  namePool: string;
  vms: [];
  typePool: string;
  queryset: any;
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

export class RemoveVMStaticPoolComponent implements OnInit, OnDestroy {

  private destroy: Subject<void> = new Subject<void>();
  public checkValid: boolean = false;

  public vms: any[] = [];
  public form = new FormGroup({
    vmsInput: new FormControl([], Validators.required)
  });

  ad_deliting = new FormControl(false);
  search = new FormControl('');

  constructor(
    private poolService: PoolDetailsService,
    private waitService: WaitService,
    private dialogRef: MatDialogRef<RemoveVMStaticPoolComponent>,
    @Inject(MAT_DIALOG_DATA) public data: IData
  ) { }
  
  ngOnInit() {
    this.load();

    this.search.valueChanges.pipe(
      debounceTime(1000)
    ).subscribe((value) => {
      this.load(value)
    })
  }

  load(value = '') {

    const props = {};

    if (value) {
      props['verbose_name'] = value;
    }

    this.poolService.getPool(this.data.idPool, {
      ...this.data.queryset,
      ...props
    }).valueChanges.pipe(map((data: any) => data.data['pool'])).subscribe((res) => {
      this.vms = res.vms || []
    });
  }

  public send(): void {
    if (!this.form.valid){
      this.checkValid = true;
      return;
    }
  
    const selectedVms = this.form.get('vmsInput').value;  

    let method = '';

    switch (this.data.typePool) {
      case 'static':
        method = 'removeVMStaticPool';
        break;
      case 'rds':
        method = 'removeVmsFromRdsPool';
        break;
      case 'automated':
        method = 'removeVmsPoolAdDeleting';
        break;
      case 'guest':
        method = 'removeVmsPoolAdDeleting';
        break;
      default:
        return;
    }
    
    if (method) {
      this.waitService.setWait(true);

      this.poolService[method](this.data.idPool, selectedVms, this.ad_deliting.value).pipe(takeUntil(this.destroy)).subscribe((res) => {
        if (res) {

          setTimeout(() => this.poolService.getPool(this.data.idPool, this.data.queryset).refetch(), 500)

          this.waitService.setWait(false);
          this.dialogRef.close();
        }
      });
    }
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
