import { Component, Inject, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';

import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { WaitService } from '@app/core/components/wait/wait.service';
import { VmActions } from '@app/shared/enums/vm-actions';
import { PoolDetailsService } from '../pool-details.service';

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
  constructor(
    private poolDetailsService: PoolDetailsService,
    private waitService: WaitService,
    private dialogRef: MatDialogRef<VmActionComponent>,
    private fb: FormBuilder,
    @Inject(MAT_DIALOG_DATA) public data: {
      idPool: string | number
      poolType: string,
      freeVm: boolean,
      action: string,
      timeout: string
    }) {
      this.data = data;
    }

  ngOnInit() {
    const {freeVm, action, timeout} = this.data;

    this.vmActionForm = this.fb.group({
      freeVm: [freeVm],
      action: [action],
      timeout: [timeout]
    })
  }

  public send(): void {
    const {
      idPool,
      poolType,
    } = this.data;
    const freeVm = this.vmActionForm.get('freeVm').value;
    const action = this.vmActionForm.get('action').value;
    const timeout = this.vmActionForm.get('timeout').value;

    this.waitService.setWait(true);
    this.poolDetailsService.setVmActions(idPool, poolType, freeVm, action, timeout).subscribe((res) => {

      if (res) {
        this.poolDetailsService.getPool( idPool ).refetch();
        this.waitService.setWait(false);
        this.dialogRef.close();
      }
    })
  }

}
