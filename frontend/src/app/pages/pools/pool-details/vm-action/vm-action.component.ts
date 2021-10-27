import { Component, Inject, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';

import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { WaitService } from '@app/core/components/wait/wait.service';
import { PoolDetailsService } from '../pool-details.service';

enum VmActions {
  None = 'Нет действия',
  Shutdown = 'Включить',
  ShutdownForced = 'Выключить форсировано',
  Suspend = 'Пауза'
}

@Component({
  selector: 'vdi-vm-action',
  templateUrl: './vm-action.component.html',
  styleUrls: ['./vm-action.component.scss']
})

export class VmActionComponent implements OnInit {
  public vmActionForm: FormGroup;
  public showTimeoutInput: boolean;

  public actions = [
    {description: VmActions.None, value: 'NONE'},
    {description: VmActions.Shutdown, value: 'SHUTDOWN'},
    {description: VmActions.ShutdownForced, value: 'SHUTDOWN_FORCED'},
    {description: VmActions.Suspend, value: 'SUSPEND'}
  ]
  constructor(private poolDetailsService: PoolDetailsService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<VmActionComponent>,
              private fb: FormBuilder,
              @Inject(MAT_DIALOG_DATA) public data: {  
                idPool: string | number
                poolType: string,
                action: string,
                timeout: string
              }) {
                this.data = data;
               }
  
  ngOnInit() {
    const {action, timeout} = this.data;
    this.showTimeoutInput = action === 'NONE' ? false : true;

    this.vmActionForm = this.fb.group({
      action: [action],
      timeout: [timeout]
    })
    this.vmActionForm.get('action').valueChanges.subscribe( (a: string) => {
      if (a === 'NONE'){
        this.showTimeoutInput = false;
        this.vmActionForm.get('timeout').setValue(0)
      }else{
        this.showTimeoutInput = true;
      }
      
    })

  }


  public send(): void {
    const {
      idPool, 
      poolType, 
    } = this.data;
    const action = this.vmActionForm.get('action').value;
    const timeout = this.vmActionForm.get('timeout').value;
    
    this.waitService.setWait(true);
    this.poolDetailsService.setVmActions( idPool, poolType, action, timeout).subscribe((res) => {
      
      if (res) {
        this.poolDetailsService.getPool( idPool, poolType).refetch();
        this.waitService.setWait(false);
        this.dialogRef.close();
      }
    })
  }




}
