import { Component, Inject } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Router } from '@angular/router';

import { WaitService } from '../../../../core/components/wait/wait.service';
import { PoolDetailsService } from '../pool-details.service';

interface IData {
  idPool: number;
  namePool: string;
  typePool: string;
}

@Component({
  selector: 'vdi-remove-pool',
  templateUrl: './remove-pool.component.html'
})

export class RemovePoolComponent  {

  ad_deliting = new FormControl(false);

  constructor(
    private poolService: PoolDetailsService,
    private waitService: WaitService,
    private dialogRef: MatDialogRef<RemovePoolComponent>,
    private router: Router,
    @Inject(MAT_DIALOG_DATA) public data: IData
  ) {}

  public send() {
    this.waitService.setWait(true);

    if (this.data.typePool === 'automated' || this.data.typePool === 'guest') {
      this.poolService.removePoolAdDeleting(this.data.idPool, this.ad_deliting.value).subscribe(() => {
        this.dialogRef.close();
        this.router.navigate(['pools']);
        this.waitService.setWait(false);
      });
    } else {
      this.poolService.removePool(this.data.idPool, true).subscribe(() => {
        this.dialogRef.close();
        this.router.navigate(['pools']);
        this.waitService.setWait(false);
      });
    }
  }
}
