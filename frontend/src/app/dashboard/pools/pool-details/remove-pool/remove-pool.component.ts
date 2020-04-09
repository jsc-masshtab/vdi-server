import { PoolsUpdateService } from './../../all-pools/pools.update.service';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject } from '@angular/core';
import { Router } from '@angular/router';
import { MAT_DIALOG_DATA } from '@angular/material';
import { PoolDetailsService } from '../pool-details.service';

interface IData {
  idPool: number;
  namePool: string;
}

@Component({
  selector: 'vdi-remove-pool',
  templateUrl: './remove-pool.component.html'
})

export class RemovePoolComponent  {

  constructor(
              private poolService: PoolDetailsService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemovePoolComponent>,
              private router: Router,
              @Inject(MAT_DIALOG_DATA) public data: IData,
              private updatePools: PoolsUpdateService) {}

  public send() {
    this.waitService.setWait(true);
    this.poolService.removePool(this.data.idPool, true).subscribe((res) => {
      if (res) {
        setTimeout(() => {
          this.dialogRef.close();
          this.router.navigate([`pools`]);
          this.updatePools.setUpdate('update');
          this.waitService.setWait(false);
        }, 1000);
      }
    });
  }
}
