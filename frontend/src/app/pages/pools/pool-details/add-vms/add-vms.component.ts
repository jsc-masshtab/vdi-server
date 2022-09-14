import { Component, Inject, OnInit, OnDestroy } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { debounceTime, map, takeUntil } from 'rxjs/operators';
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

  public vms: any[] = [];
  public vmsInput = new FormControl([], Validators.required);

  search = new FormControl('');

  private destroy$: Subject<any> = new Subject<any>();

  constructor(
    private poolService: PoolDetailsService,
    private waitService: WaitService,
    private dialogRef: MatDialogRef<AddVMStaticPoolComponent>,
    @Inject(MAT_DIALOG_DATA) public data: IData
  ) {}

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
    
    this.poolService.getAllVms(this.data.idController, this.data.idResourcePool, props).valueChanges.pipe(map((data: any) => data.data.controller['vms'])).subscribe((res) => {
      this.vms = [...res]
    });
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

  public selectAllVms(vms: any[]): void { 
    this.vmsInput.setValue(vms);
  }

  public deselectAllVms(){
    this.vmsInput.setValue([]);
  }

  ngOnDestroy() {    
    this.destroy$.next();
  }
}
