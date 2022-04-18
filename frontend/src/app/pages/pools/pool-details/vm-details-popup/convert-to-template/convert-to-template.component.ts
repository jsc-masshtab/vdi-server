import { Component, Inject } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialog, MAT_DIALOG_DATA } from '@angular/material/dialog';

import { WaitService } from '../../../../../core/components/wait/wait.service';
import { PoolDetailsService } from '../../pool-details.service';
import { VmDetailsPopupService } from '../vm-details-popup.service';



@Component({
  selector: 'convert-to-template',
  templateUrl: './convert-to-template.component.html'
})

export class ConvertToTemaplteComponent {

  verbose_name = new FormControl('');
  
  constructor(private waitService: WaitService,
              private vmDetailsPopupService: VmDetailsPopupService,
              private poolService: PoolDetailsService,
              public dialog: MatDialog,
              @Inject(MAT_DIALOG_DATA) public data,
            ) {}

  public send() {
    this.waitService.setWait(true);

    const data = {
      verbose_name: this.verbose_name.value,
      controller_id: this.data.controller_id
    }

    this.vmDetailsPopupService.convertToTemplate(this.data.vm_id, data).subscribe((res) => {
      if (res) {
        this.poolService.getPool(this.data.pool.idPool).refetch();
        this.waitService.setWait(false);
        this.dialog.closeAll();
      }
    });
  }
}
